#include "engine/AssetPackIndex.h"
#include "engine/update/AppInstallation.h"
#include "engine/update/AppUpdater.h"
#include "engine/update/ReleaseManifest.h"
#include "engine/update/Sha256.h"

#include <doctest/doctest.h>
#include <monocypher-ed25519.h>

#include <algorithm>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <map>
#include <mutex>
#include <sstream>
#include <string>
#include <tuple>
#include <vector>

namespace
{
using OpenYAMM::Engine::AppInstallation;
using OpenYAMM::Engine::AppUpdater;
using OpenYAMM::Engine::GameExecutableName;
using OpenYAMM::Engine::LauncherCopyName;
using OpenYAMM::Engine::LauncherExecutableName;
using OpenYAMM::Engine::ManifestPublicKey;
using OpenYAMM::Engine::programDirectory;
using OpenYAMM::Engine::UpdateState;

constexpr const char *BaseUrl = "https://updates.invalid/openyamm/updates/";

std::filesystem::path makeTemporaryRoot()
{
    const uint64_t tickCount = uint64_t(std::chrono::steady_clock::now().time_since_epoch().count());
    return std::filesystem::temp_directory_path() / ("openyamm_updater_" + std::to_string(tickCount));
}

void writeFile(const std::filesystem::path &path, const std::string &contents)
{
    std::filesystem::create_directories(path.parent_path());
    std::ofstream file(path, std::ios::binary);
    file << contents;
}

std::string readFile(const std::filesystem::path &path)
{
    std::ifstream file(path, std::ios::binary);
    return std::string(std::istreambuf_iterator<char>(file), std::istreambuf_iterator<char>());
}

std::string hex(const uint8_t *pBytes, size_t size)
{
    constexpr const char *pDigits = "0123456789abcdef";
    std::string text;

    for (size_t index = 0; index < size; ++index)
    {
        text.push_back(pDigits[pBytes[index] >> 4]);
        text.push_back(pDigits[pBytes[index] & 0xf]);
    }

    return text;
}

std::vector<uint8_t> unhex(const std::string &text)
{
    std::vector<uint8_t> bytes;

    for (size_t index = 0; index + 1 < text.size(); index += 2)
    {
        bytes.push_back(uint8_t(std::stoi(text.substr(index, 2), nullptr, 16)));
    }

    return bytes;
}

std::string base64(const uint8_t *pBytes, size_t size)
{
    constexpr const char *pAlphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    std::string text;

    for (size_t index = 0; index < size; index += 3)
    {
        const uint32_t value = uint32_t(pBytes[index]) << 16 | (index + 1 < size ? uint32_t(pBytes[index + 1]) << 8 : 0)
            | (index + 2 < size ? uint32_t(pBytes[index + 2]) : 0);
        text.push_back(pAlphabet[(value >> 18) & 63]);
        text.push_back(pAlphabet[(value >> 12) & 63]);
        text.push_back(index + 1 < size ? pAlphabet[(value >> 6) & 63] : '=');
        text.push_back(index + 2 < size ? pAlphabet[value & 63] : '=');
    }

    return text;
}

struct TestSigner
{
    uint8_t secretKey[64] = {};
    ManifestPublicKey publicKey;

    TestSigner()
    {
        uint8_t seed[32];

        for (size_t index = 0; index < 32; ++index)
        {
            seed[index] = uint8_t(index * 7 + 3);
        }

        publicKey.slot = 1;
        crypto_ed25519_key_pair(secretKey, publicKey.key.data(), seed);
    }

    std::string sign(const std::string &message, int slot = 1) const
    {
        uint8_t signature[64];
        crypto_ed25519_sign(signature, secretKey, reinterpret_cast<const uint8_t *>(message.data()), message.size());
        return "{\"key\": " + std::to_string(slot) + ", \"algorithm\": \"ed25519\", \"signature\": \""
            + base64(signature, sizeof(signature)) + "\"}\n";
    }
};

uint32_t crc32(const std::string &data)
{
    uint32_t crc = 0xffffffffu;

    for (const unsigned char byte : data)
    {
        crc ^= byte;

        for (int bit = 0; bit < 8; ++bit)
        {
            crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1u)));
        }
    }

    return ~crc;
}

void putLittleEndian(std::string &out, uint32_t value, int bytes)
{
    for (int index = 0; index < bytes; ++index)
    {
        out.push_back(char((value >> (8 * index)) & 0xff));
    }
}

// A zip of stored entries, as publish_release.py's app archive would hold them.
std::string storedZip(const std::map<std::string, std::string> &entries)
{
    std::string archive;
    std::string directory;

    for (const auto &[name, data] : entries)
    {
        const uint32_t offset = uint32_t(archive.size());
        const uint32_t checksum = crc32(data);
        putLittleEndian(archive, 0x04034b50, 4);
        putLittleEndian(archive, 20, 2);
        putLittleEndian(archive, 0, 2);
        putLittleEndian(archive, 0, 2);
        putLittleEndian(archive, 0, 4);
        putLittleEndian(archive, checksum, 4);
        putLittleEndian(archive, uint32_t(data.size()), 4);
        putLittleEndian(archive, uint32_t(data.size()), 4);
        putLittleEndian(archive, uint32_t(name.size()), 2);
        putLittleEndian(archive, 0, 2);
        archive += name;
        archive += data;
        putLittleEndian(directory, 0x02014b50, 4);
        putLittleEndian(directory, 20, 2);
        putLittleEndian(directory, 20, 2);
        putLittleEndian(directory, 0, 2);
        putLittleEndian(directory, 0, 2);
        putLittleEndian(directory, 0, 4);
        putLittleEndian(directory, checksum, 4);
        putLittleEndian(directory, uint32_t(data.size()), 4);
        putLittleEndian(directory, uint32_t(data.size()), 4);
        putLittleEndian(directory, uint32_t(name.size()), 2);
        putLittleEndian(directory, 0, 2);
        putLittleEndian(directory, 0, 2);
        putLittleEndian(directory, 0, 2);
        putLittleEndian(directory, 0, 2);
        putLittleEndian(directory, 0, 4);
        putLittleEndian(directory, offset, 4);
        directory += name;
    }

    const uint32_t directoryOffset = uint32_t(archive.size());
    archive += directory;
    putLittleEndian(archive, 0x06054b50, 4);
    putLittleEndian(archive, 0, 2);
    putLittleEndian(archive, 0, 2);
    putLittleEndian(archive, uint32_t(entries.size()), 2);
    putLittleEndian(archive, uint32_t(entries.size()), 2);
    putLittleEndian(archive, uint32_t(directory.size()), 4);
    putLittleEndian(archive, directoryOffset, 4);
    putLittleEndian(archive, 0, 2);
    return archive;
}

// Serves files below a folder for URLs below BaseUrl, honouring ranges; can cut a transfer short once, or answer
// HTTP 503 a number of times as nginx does above its connections per address.
class FolderTransport final : public OpenYAMM::Engine::HttpTransport
{
public:
    struct Log
    {
        std::mutex mutex;
        std::vector<std::pair<std::string, uint64_t>> requests;
        std::map<std::string, size_t> cutAfter;
        std::map<std::string, int> busyFor;
    };

    FolderTransport(std::filesystem::path root, std::shared_ptr<Log> log)
        : m_root(std::move(root))
        , m_log(std::move(log))
    {
    }

    int get(const std::string &url, uint64_t offset, const Sink &sink, std::string &error) override
    {
        std::string relative = url.substr(std::string(BaseUrl).size());
        size_t cut = std::string::npos;

        {
            std::lock_guard<std::mutex> lock(m_log->mutex);
            m_log->requests.emplace_back(relative, offset);
            const auto found = m_log->cutAfter.find(relative);

            if (found != m_log->cutAfter.end())
            {
                cut = found->second;
                m_log->cutAfter.erase(found);
            }

            const auto busy = m_log->busyFor.find(relative);

            if (busy != m_log->busyFor.end() && busy->second > 0)
            {
                --busy->second;
                error = "HTTP 503";
                return 503;
            }
        }

        const std::filesystem::path path = m_root / relative;

        if (!std::filesystem::is_regular_file(path))
        {
            error = "HTTP 404";
            return 404;
        }

        const std::string data = readFile(path);
        const std::string body = data.substr(std::min<size_t>(offset, data.size()));

        if (cut != std::string::npos)
        {
            sink(body.data(), std::min(cut, body.size()));
            error = "connection reset";
            return 0;
        }

        if (!body.empty() && !sink(body.data(), body.size()))
        {
            error = "cancelled";
            return 0;
        }

        return offset > 0 ? 206 : 200;
    }

private:
    std::filesystem::path m_root;
    std::shared_ptr<FolderTransport::Log> m_log;
};

struct Pack
{
    std::string id;
    std::string file;
    std::string data;
};

std::string indexJson(const std::string &release, const std::vector<Pack> &packs)
{
    std::string json = "{\"schema\": 1, \"release\": \"" + release + "\", \"build\": \"" + release
        + "\", \"profile\": \"desktop\", \"content_format\": 1, \"store\": \"../../assets/packs\", \"packs\": [";

    for (size_t index = 0; index < packs.size(); ++index)
    {
        const Pack &pack = packs[index];
        json += std::string(index > 0 ? ", " : "") + "{\"id\": \"" + pack.id + "\", \"package\": \"engine\", "
            + "\"mount\": \"/engine\", \"file\": \"" + pack.file + "\", \"size\": " + std::to_string(pack.data.size())
            + ", \"content_id\": \"c-" + pack.file + "\", \"sha256\": \""
            + OpenYAMM::Engine::sha256Hex(pack.data.data(), pack.data.size()) + "\"}";
    }

    return json + "]}";
}

// A server folder holding one release: signed manifest, app archive and packs, laid out like the master tree.
std::string publishRelease(const std::filesystem::path &server, const TestSigner &signer, const std::string &release,
                           const std::vector<Pack> &packs, const std::string &executable)
{
    const std::string archive = storedZip({
        {std::string("OpenYAMM/") + LauncherExecutableName, "launcher " + release},
        {"OpenYAMM/app/current", release + "\n"},
        {"OpenYAMM/app/" + release + "/" + GameExecutableName, executable},
        {"OpenYAMM/app/" + release + "/" + LauncherCopyName, "launcher " + release},
        {"OpenYAMM/app/" + release + "/index.json", indexJson(release, packs)},
        {"OpenYAMM/app/" + release + "/runtime/shaders/glsl/vs_model.bin", "shader"},
    });
    const std::string archiveSha = OpenYAMM::Engine::sha256Hex(archive.data(), archive.size());
    writeFile(server / "apps" / (archiveSha + ".zip"), archive);
    std::string manifest = "{\"schema\": 1, \"channel\": \"stable\", \"platform\": \"windows-x64\", \"release\": \""
        + release + "\", \"build\": \"" + release + "\", \"published\": \"2026-10-19T10:00:00Z\", "
        + "\"content_format\": 1, \"min_updater_schema\": 1, \"notes_url\": null, \"app\": {\"file\": \"app.zip\", "
        + "\"url\": \"apps/" + archiveSha + ".zip\", \"size\": " + std::to_string(archive.size()) + ", \"sha256\": \""
        + archiveSha + "\", \"android_version_code\": null}, \"packs\": [";

    for (size_t index = 0; index < packs.size(); ++index)
    {
        const Pack &pack = packs[index];
        const std::string sha = OpenYAMM::Engine::sha256Hex(pack.data.data(), pack.data.size());
        writeFile(server / "packs" / (sha + ".zip"), pack.data);
        manifest += std::string(index > 0 ? ", " : "") + "{\"id\": \"" + pack.id
            + "\", \"package\": \"engine\", \"mount\": \"/engine\", \"file\": \"" + pack.file + "\", \"url\": \"packs/"
            + sha + ".zip\", \"size\": " + std::to_string(pack.data.size()) + ", \"content_id\": \"c-" + pack.file
            + "\", \"sha256\": \"" + sha + "\"}";
    }

    manifest += "]}\n";
    writeFile(server / "channels" / "stable" / "windows-x64.json", manifest);
    writeFile(server / "channels" / "stable" / "windows-x64.json.sig", signer.sign(manifest));
    return manifest;
}

// An extracted package of a release: complete, or the small download package without its packs.
void installRelease(const std::filesystem::path &root, const std::string &release, const std::vector<Pack> &packs,
                    bool withPacks = true)
{
    writeFile(root / LauncherExecutableName, "launcher " + release);
    writeFile(root / "app" / "current", release + "\n");
    writeFile(root / "app" / release / GameExecutableName, "game " + release);
    writeFile(root / "app" / release / "index.json", indexJson(release, packs));

    for (const Pack &pack : withPacks ? packs : std::vector<Pack>())
    {
        writeFile(root / "assets" / "packs" / pack.file, pack.data);
    }
}

std::unique_ptr<AppUpdater> makeUpdater(const std::filesystem::path &install, const std::filesystem::path &server,
                                        const TestSigner &signer, std::shared_ptr<FolderTransport::Log> log)
{
    auto updater = std::make_unique<AppUpdater>(AppInstallation(install), "1.0", "windows-x64", BaseUrl,
                                                std::make_unique<FolderTransport>(server, std::move(log)));
    updater->setTrustedKeys({signer.publicKey});
    return updater;
}

const std::vector<Pack> ReleaseOnePacks = {
    {"engine.core", "engine.core-aaaa.zip", std::string(5000, 'c')},
    {"engine.models.0", "engine.models.0-bbbb.zip", std::string(70000, 'm')},
};
const std::vector<Pack> ReleaseTwoPacks = {
    {"engine.core", "engine.core-cccc.zip", std::string(6000, 'C')},
    {"engine.models.0", "engine.models.0-bbbb.zip", std::string(70000, 'm')},
};
}

TEST_CASE("sha256 matches the FIPS 180-2 examples, also when streamed")
{
    CHECK(OpenYAMM::Engine::sha256Hex("", 0) == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
    CHECK(OpenYAMM::Engine::sha256Hex("abc", 3) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
    const std::string message = "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq";
    CHECK(OpenYAMM::Engine::sha256Hex(message.data(), message.size())
          == "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1");
    OpenYAMM::Engine::Sha256 streamed;
    const std::string million(1000000, 'a');

    for (size_t offset = 0; offset < million.size(); offset += 999)
    {
        streamed.update(million.data() + offset, std::min<size_t>(999, million.size() - offset));
    }

    CHECK(streamed.finishHex() == "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0");
}

TEST_CASE("manifest signatures verify with RFC 8032 Ed25519 and reject changes and unknown keys")
{
    // RFC 8032, 7.1, TEST 2: the signature Python's cryptography (publish_release.py) also produces.
    ManifestPublicKey key;
    key.slot = 1;
    const std::vector<uint8_t> publicKey = unhex("3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c");
    std::copy(publicKey.begin(), publicKey.end(), key.key.begin());
    const std::vector<uint8_t> signature = unhex("92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da"
                                                 "085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00");
    const std::string message(1, char(0x72));
    const std::string signatureJson = "{\"key\": 1, \"algorithm\": \"ed25519\", \"signature\": \""
        + base64(signature.data(), signature.size()) + "\"}";
    std::string error;
    CHECK(OpenYAMM::Engine::verifyManifestSignature(message, signatureJson, {key}, error) == 1);
    CHECK_FALSE(OpenYAMM::Engine::verifyManifestSignature(std::string(1, char(0x73)), signatureJson, {key}, error));
    key.slot = 2;
    CHECK_FALSE(OpenYAMM::Engine::verifyManifestSignature(message, signatureJson, {key}, error));
    CHECK(error.find("unknown key") != std::string::npos);
}

TEST_CASE("the compiled manifest keys are the committed public keys")
{
    for (const ManifestPublicKey &key : OpenYAMM::Engine::releaseManifestPublicKeys())
    {
        const std::filesystem::path path = std::filesystem::path(OPENYAMM_SOURCE_DIR) / "packaging" / "keys"
            / ("manifest-ed25519-" + std::to_string(key.slot) + ".pub");
        std::string committed = readFile(path);
        committed.erase(committed.find_last_not_of(" \r\n") + 1);
        CHECK(hex(key.key.data(), key.key.size()) == committed);
    }
}

TEST_CASE("release versions compare numerically and development builds do not compare")
{
    CHECK(OpenYAMM::Engine::compareReleaseVersions("1.6", "1.5") == 1);
    CHECK(OpenYAMM::Engine::compareReleaseVersions("1.10", "1.9") == 1);
    CHECK(OpenYAMM::Engine::compareReleaseVersions("2.0", "2.0") == 0);
    CHECK(OpenYAMM::Engine::compareReleaseVersions("0.9", "1.0") == -1);
    CHECK_FALSE(OpenYAMM::Engine::compareReleaseVersions("nightly", "1.0"));
    CHECK_FALSE(OpenYAMM::Engine::compareReleaseVersions("1.05", "1.0"));
    CHECK_FALSE(OpenYAMM::Engine::compareReleaseVersions("1.6.1", "1.0"));
}

TEST_CASE("manifests address store files by hash and keep packs inside their package")
{
    const std::filesystem::path server = makeTemporaryRoot();
    const std::string manifest = publishRelease(server, TestSigner(), "1.1", ReleaseTwoPacks, "game");
    std::string error;
    const std::optional<OpenYAMM::Engine::ReleaseManifest> parsed =
        OpenYAMM::Engine::parseReleaseManifest(manifest, error);
    REQUIRE_MESSAGE(parsed.has_value(), error);
    CHECK(parsed->release == "1.1");
    CHECK(parsed->packs.size() == 2);
    CHECK_FALSE(parsed->androidVersionCode.has_value());
    CHECK(parsed->notes.empty());

    std::string withNotes = manifest;
    withNotes.replace(withNotes.find("\"notes_url\": null"), 17, "\"notes_url\": null, \"notes\": \"Faster loading.\"");
    const std::optional<OpenYAMM::Engine::ReleaseManifest> noted =
        OpenYAMM::Engine::parseReleaseManifest(withNotes, error);
    REQUIRE_MESSAGE(noted.has_value(), error);
    CHECK(noted->notes == "Faster loading.");

    std::string escaped = manifest;
    escaped.replace(escaped.find("\"url\": \"packs/"), 14, "\"url\": \"../x/");
    CHECK_FALSE(OpenYAMM::Engine::parseReleaseManifest(escaped, error));

    std::string outside = manifest;
    outside.replace(outside.find("\"mount\": \"/engine\""), 18, "\"mount\": \"/worlds/mm6\"");
    CHECK_FALSE(OpenYAMM::Engine::parseReleaseManifest(outside, error));

    // A mirror's absolute https address still names the file by its hash.
    const std::string packSha = OpenYAMM::Engine::sha256Hex(ReleaseTwoPacks[0].data.data(), 6000);
    const size_t packUrl = manifest.find("\"url\": \"packs/" + packSha);
    std::string mirrored = manifest;
    mirrored.replace(packUrl, 14, "\"url\": \"https://mirror.example/openyamm/");
    const std::optional<OpenYAMM::Engine::ReleaseManifest> mirror =
        OpenYAMM::Engine::parseReleaseManifest(mirrored, error);
    REQUIRE_MESSAGE(mirror.has_value(), error);
    CHECK(OpenYAMM::Engine::releaseFileUrl(BaseUrl, mirror->packUrls[0])
          == "https://mirror.example/openyamm/" + packSha + ".zip");
    CHECK(OpenYAMM::Engine::releaseFileUrl(BaseUrl, mirror->packUrls[1]).starts_with(std::string(BaseUrl) + "packs/"));

    std::string insecure = manifest;
    insecure.replace(packUrl, 14, "\"url\": \"http://mirror.example/");
    CHECK_FALSE(OpenYAMM::Engine::parseReleaseManifest(insecure, error));
    std::string misnamed = manifest;
    misnamed.replace(packUrl, 14 + 64, "\"url\": \"https://mirror.example/" + std::string(64, 'a'));
    CHECK_FALSE(OpenYAMM::Engine::parseReleaseManifest(misnamed, error));
    std::filesystem::remove_all(server);
}

TEST_CASE("the launcher rolls a version back after two starts that never reached the main menu")
{
    const std::filesystem::path root = makeTemporaryRoot();
    installRelease(root, "1.0", ReleaseOnePacks);
    writeFile(root / "app" / "1.1" / GameExecutableName, "game 1.1");
    AppInstallation installation(root);
    std::string error;
    REQUIRE(installation.switchTo("1.1", error));
    CHECK(installation.previousVersion() == "1.0");

    std::string rolledBack;
    CHECK(installation.chooseVersionToStart(rolledBack) == "1.1");
    CHECK(installation.chooseVersionToStart(rolledBack) == "1.1");
    CHECK(rolledBack.empty());
    CHECK(installation.chooseVersionToStart(rolledBack) == "1.0");
    CHECK(rolledBack == "1.1");
    CHECK(installation.currentVersion() == "1.0");
    CHECK(installation.takeRollbackNotice() == "1.1");
    CHECK_FALSE(installation.takeRollbackNotice());

    // A version that reached its main menu once is never rolled back.
    REQUIRE(installation.switchTo("1.1", error));
    CHECK(installation.markHealthy("1.1"));

    for (int start = 0; start < 4; ++start)
    {
        CHECK(installation.chooseVersionToStart(rolledBack) == "1.1");
    }

    CHECK(AppInstallation::containing(root / "app" / "1.1")->root() == root);
    CHECK_FALSE(AppInstallation::containing(root / "build" / "game"));
    std::filesystem::remove_all(root);
}

TEST_CASE("the program folder of a macOS app bundle is the folder that holds the bundle")
{
    CHECK(programDirectory("/Users/a/OpenYAMM/app/1.9/OpenYAMM.app/Contents/Resources/")
          == std::filesystem::path("/Users/a/OpenYAMM/app/1.9"));
    CHECK(programDirectory("/opt/OpenYAMM/app/1.9/") == std::filesystem::path("/opt/OpenYAMM/app/1.9"));
    CHECK(programDirectory("/opt/OpenYAMM/app/1.9") == std::filesystem::path("/opt/OpenYAMM/app/1.9"));
    CHECK(programDirectory("/opt/game/Contents/Resources/") == std::filesystem::path("/opt/game/Contents/Resources"));
}

TEST_CASE("an update downloads only changed packs, resumes broken transfers and cleans up after a healthy start")
{
    const std::filesystem::path root = makeTemporaryRoot();
    const std::filesystem::path install = root / "OpenYAMM";
    const std::filesystem::path server = root / "server";
    const TestSigner signer;
    installRelease(install, "1.0", ReleaseOnePacks);
    publishRelease(server, signer, "1.1", ReleaseTwoPacks, "game 1.1");
    auto log = std::make_shared<FolderTransport::Log>();
    log->cutAfter["packs/" + OpenYAMM::Engine::sha256Hex(ReleaseTwoPacks[0].data.data(), 6000) + ".zip"] = 2500;
    std::unique_ptr<AppUpdater> updater = makeUpdater(install, server, signer, log);

    updater->check();
    updater->wait();
    REQUIRE_MESSAGE(updater->status().state == UpdateState::Available, updater->status().message);
    CHECK(updater->status().release == "1.1");
    CHECK(updater->status().packCount == 1);

    updater->download();
    updater->wait();
    REQUIRE_MESSAGE(updater->status().state == UpdateState::Ready, updater->status().message);
    CHECK(updater->status().doneBytes == updater->status().totalBytes);
    // The unchanged pack was never requested; the cut transfer resumed at its byte 2500.
    bool resumed = false;

    for (const auto &[url, offset] : log->requests)
    {
        CHECK(url.find(OpenYAMM::Engine::sha256Hex(ReleaseTwoPacks[1].data.data(), 70000)) == std::string::npos);
        resumed = resumed || offset == 2500;
    }

    CHECK(resumed);
    // Nothing the running version uses changed before the switch.
    CHECK(AppInstallation(install).currentVersion() == "1.0");

    std::string error;
    REQUIRE(updater->activate(error));
    AppInstallation installation(install);
    CHECK(installation.currentVersion() == "1.1");
    CHECK(installation.previousVersion() == "1.0");
    CHECK(readFile(install / "app" / "1.1" / GameExecutableName) == "game 1.1");
    CHECK_FALSE(std::filesystem::exists(install / "update"));
#if !defined(_WIN32)
    // Zip archives carry no permissions; the staged executables are made executable.
    const std::filesystem::perms permissions =
        std::filesystem::status(install / "app" / "1.1" / GameExecutableName).permissions();
    CHECK((permissions & std::filesystem::perms::owner_exec) != std::filesystem::perms::none);
#endif

    writeFile(install / "assets" / "engine.zip", "release 1.5 package");
    std::ostringstream cleanupLog;
    OpenYAMM::Engine::finishHealthyStart(installation, "1.1", cleanupLog);
    CHECK(installation.isHealthy("1.1"));
    CHECK_FALSE(installation.previousVersion());
    CHECK_FALSE(std::filesystem::exists(install / "app" / "1.0"));
    CHECK_FALSE(std::filesystem::exists(install / "assets" / "packs" / "engine.core-aaaa.zip"));
    CHECK(std::filesystem::exists(install / "assets" / "packs" / "engine.core-cccc.zip"));
    CHECK(std::filesystem::exists(install / "assets" / "packs" / "engine.models.0-bbbb.zip"));
    CHECK_FALSE(std::filesystem::exists(install / "assets" / "engine.zip"));
    CHECK(readFile(install / LauncherExecutableName) == "launcher 1.1");
    std::filesystem::remove_all(root);
}

TEST_CASE("an update waits out a busy server and gives up on a missing file")
{
    const std::filesystem::path root = makeTemporaryRoot();
    const std::filesystem::path install = root / "OpenYAMM";
    const std::filesystem::path server = root / "server";
    const TestSigner signer;
    installRelease(install, "1.0", ReleaseOnePacks);
    publishRelease(server, signer, "1.1", ReleaseTwoPacks, "game 1.1");
    const std::string pack = "packs/" + OpenYAMM::Engine::sha256Hex(ReleaseTwoPacks[0].data.data(), 6000) + ".zip";
    auto log = std::make_shared<FolderTransport::Log>();
    // Two refusals: the second retry, after the first pause, gets the file.
    log->busyFor[pack] = 2;
    std::unique_ptr<AppUpdater> updater = makeUpdater(install, server, signer, log);
    updater->check();
    updater->wait();
    REQUIRE(updater->status().state == UpdateState::Available);
    updater->download();
    updater->wait();
    CHECK_MESSAGE(updater->status().state == UpdateState::Ready, updater->status().message);
    CHECK(std::count_if(log->requests.begin(), log->requests.end(),
                        [&pack](const auto &request) { return request.first == pack; }) == 3);

    // A missing file is not asked for again.
    const std::filesystem::path other = makeTemporaryRoot();
    installRelease(other / "OpenYAMM", "1.0", ReleaseOnePacks);
    std::filesystem::remove(server / pack);
    log->requests.clear();
    updater = makeUpdater(other / "OpenYAMM", server, signer, log);
    updater->check();
    updater->wait();
    REQUIRE(updater->status().state == UpdateState::Available);
    updater->download();
    updater->wait();
    CHECK(updater->status().state == UpdateState::Failed);
    CHECK(updater->status().message.find("HTTP 404") != std::string::npos);
    CHECK(std::count_if(log->requests.begin(), log->requests.end(),
                        [&pack](const auto &request) { return request.first == pack; }) == 1);
    std::filesystem::remove_all(other);
    std::filesystem::remove_all(root);
}

TEST_CASE("an update refuses bad signatures, damaged files and replayed older releases")
{
    const std::filesystem::path root = makeTemporaryRoot();
    const std::filesystem::path install = root / "OpenYAMM";
    const std::filesystem::path server = root / "server";
    const TestSigner signer;
    installRelease(install, "1.0", ReleaseOnePacks);
    const std::string manifest = publishRelease(server, signer, "1.1", ReleaseTwoPacks, "game 1.1");
    auto log = std::make_shared<FolderTransport::Log>();

    // A manifest changed after signing.
    std::string tampered = manifest;
    tampered.replace(tampered.find("\"1.1\""), 5, "\"1.2\"");
    writeFile(server / "channels" / "stable" / "windows-x64.json", tampered);
    std::unique_ptr<AppUpdater> updater = makeUpdater(install, server, signer, log);
    updater->check();
    updater->wait();
    CHECK(updater->status().state == UpdateState::Failed);
    CHECK(updater->status().message.find("signature") != std::string::npos);

    // A pack whose bytes do not match the signed manifest, on both attempts.
    writeFile(server / "channels" / "stable" / "windows-x64.json", manifest);
    const std::string packSha = OpenYAMM::Engine::sha256Hex(ReleaseTwoPacks[0].data.data(), 6000);
    writeFile(server / "packs" / (packSha + ".zip"), std::string(6000, 'X'));
    updater = makeUpdater(install, server, signer, log);
    updater->check();
    updater->wait();
    REQUIRE(updater->status().state == UpdateState::Available);
    updater->download();
    updater->wait();
    CHECK(updater->status().state == UpdateState::Failed);
    CHECK(updater->status().message.find("verification") != std::string::npos);
    CHECK_FALSE(std::filesystem::exists(install / "assets" / "packs" / "engine.core-cccc.zip"));
    CHECK(AppInstallation(install).currentVersion() == "1.0");

    // A validly signed but older release.
    publishRelease(server, signer, "0.9", ReleaseOnePacks, "game 0.9");
    updater = makeUpdater(install, server, signer, log);
    updater->check();
    updater->wait();
    CHECK(updater->status().state == UpdateState::UpToDate);
    std::filesystem::remove_all(root);
}

TEST_CASE("a fresh installation from the small package downloads its own content, or a newer release")
{
    const std::filesystem::path root = makeTemporaryRoot();
    const std::filesystem::path install = root / "OpenYAMM";
    const std::filesystem::path server = root / "server";
    const TestSigner signer;
    installRelease(install, "1.0", ReleaseOnePacks, false);
    publishRelease(server, signer, "1.0", ReleaseOnePacks, "game 1.0");
    auto log = std::make_shared<FolderTransport::Log>();
    std::unique_ptr<AppUpdater> updater = makeUpdater(install, server, signer, log);

    updater->check();
    updater->wait();
    REQUIRE_MESSAGE(updater->status().state == UpdateState::Available, updater->status().message);
    CHECK(updater->status().contentOnly);
    CHECK(updater->status().packCount == 2);
    CHECK(updater->status().totalBytes == 75000);

    updater->download();
    updater->wait();
    REQUIRE_MESSAGE(updater->status().state == UpdateState::Ready, updater->status().message);

    for (const auto &[url, offset] : log->requests)
    {
        CHECK(url.find("/apps/") == std::string::npos);
    }

    std::string error;
    REQUIRE(updater->activate(error));
    AppInstallation installation(install);
    CHECK(installation.currentVersion() == "1.0");
    CHECK_FALSE(installation.previousVersion());
    CHECK(readFile(install / "assets" / "packs" / "engine.models.0-bbbb.zip") == ReleaseOnePacks[1].data);

    // Complete now: nothing more to download.
    updater = makeUpdater(install, server, signer, log);
    updater->check();
    updater->wait();
    CHECK(updater->status().state == UpdateState::UpToDate);

    // A package whose index names other packs than the published release cannot be completed.
    const std::filesystem::path stale = root / "stale";
    installRelease(stale, "1.0", ReleaseTwoPacks, false);
    updater = makeUpdater(stale, server, signer, log);
    updater->check();
    updater->wait();
    CHECK(updater->status().state == UpdateState::Failed);
    CHECK(updater->status().message.find("does not match") != std::string::npos);

    // When a newer release is out, a fresh installation installs that one instead.
    publishRelease(server, signer, "1.1", ReleaseTwoPacks, "game 1.1");
    updater = makeUpdater(stale, server, signer, log);
    updater->check();
    updater->wait();
    REQUIRE_MESSAGE(updater->status().state == UpdateState::Available, updater->status().message);
    CHECK_FALSE(updater->status().contentOnly);
    updater->download();
    updater->wait();
    REQUIRE_MESSAGE(updater->status().state == UpdateState::Ready, updater->status().message);
    REQUIRE(updater->activate(error));
    CHECK(AppInstallation(stale).currentVersion() == "1.1");
    std::filesystem::remove_all(root);
}

TEST_CASE("an empty installation installs the downloaded app's release with its launcher, or a newer release")
{
    const std::filesystem::path root = makeTemporaryRoot();
    const std::filesystem::path install = root / "Application Support" / "OpenYAMM";
    const std::filesystem::path server = root / "server";
    const TestSigner signer;
    publishRelease(server, signer, "1.0", ReleaseOnePacks, "game 1.0");
    auto log = std::make_shared<FolderTransport::Log>();
    std::unique_ptr<AppUpdater> updater = makeUpdater(install, server, signer, log);

    updater->check();
    updater->wait();
    REQUIRE_MESSAGE(updater->status().state == UpdateState::Available, updater->status().message);
    CHECK_FALSE(updater->status().contentOnly);
    CHECK(updater->status().packCount == 2);
    CHECK(updater->status().totalBytes > 75000);

    updater->download();
    updater->wait();
    REQUIRE_MESSAGE(updater->status().state == UpdateState::Ready, updater->status().message);
    std::string error;
    REQUIRE_MESSAGE(updater->activate(error), error);
    AppInstallation installation(install);
    CHECK(installation.currentVersion() == "1.0");
    CHECK(readFile(installation.gameExecutable("1.0")) == "game 1.0");
    CHECK(readFile(installation.launcherPath()) == "launcher 1.0");
    CHECK(readFile(install / "assets" / "packs" / "engine.core-aaaa.zip") == ReleaseOnePacks[0].data);

    // Installed: the same release is up to date.
    updater = makeUpdater(install, server, signer, log);
    updater->check();
    updater->wait();
    CHECK(updater->status().state == UpdateState::UpToDate);

    // An app newer than the published release finds nothing to install.
    AppUpdater newer(AppInstallation(root / "newer"), "1.1", "windows-x64", BaseUrl,
                     std::make_unique<FolderTransport>(server, log));
    newer.setTrustedKeys({signer.publicKey});
    newer.check();
    newer.wait();
    CHECK(newer.status().state == UpdateState::UpToDate);

    // An older app installs the newer published release.
    publishRelease(server, signer, "1.1", ReleaseTwoPacks, "game 1.1");
    const std::filesystem::path other = root / "other";
    updater = makeUpdater(other, server, signer, log);
    updater->check();
    updater->wait();
    REQUIRE_MESSAGE(updater->status().state == UpdateState::Available, updater->status().message);
    updater->download();
    updater->wait();
    REQUIRE_MESSAGE(updater->status().state == UpdateState::Ready, updater->status().message);
    REQUIRE_MESSAGE(updater->activate(error), error);
    CHECK(AppInstallation(other).currentVersion() == "1.1");
    CHECK(readFile(AppInstallation(other).launcherPath()) == "launcher 1.1");
    std::filesystem::remove_all(root);
}

TEST_CASE("the packager writes the content format this binary reads")
{
    const std::string packager =
        readFile(std::filesystem::path(OPENYAMM_SOURCE_DIR) / "tools" / "package_runtime_assets.py");
    const std::string expected =
        "\nCONTENT_FORMAT = " + std::to_string(OpenYAMM::Engine::SupportedContentFormat) + "\n";
    CHECK(packager.find(expected) != std::string::npos);
}

TEST_CASE("an update plans a language's optional packs only for the languages kept installed")
{
    OpenYAMM::Engine::ReleaseManifest manifest;
    manifest.app.size = 100;

    for (const auto &[pId, pLanguage, size] :
         {std::tuple{"engine.core", "", 10}, std::tuple{"lang-ru.engine.audio", "ru", 20},
          std::tuple{"lang-zh-cn.engine.fonts", "zh-cn", 40}})
    {
        OpenYAMM::Engine::AssetPackRecord pack;
        pack.id = pId;
        pack.file = std::string(pId) + ".zip";
        pack.size = uint64_t(size);
        pack.language = pLanguage;
        manifest.packs.push_back(pack);
        manifest.packUrls.push_back("packs/" + pack.file);
    }

    const std::filesystem::path store = makeTemporaryRoot();
    CHECK(OpenYAMM::Engine::planUpdate(manifest, store, false).downloadBytes == 10);
    CHECK(OpenYAMM::Engine::planUpdate(manifest, store, false, {"ru"}).downloadBytes == 30);
    CHECK(OpenYAMM::Engine::planUpdate(manifest, store, true, {"ru", "zh-cn"}).downloadBytes == 170);
    std::filesystem::remove_all(store);
}
