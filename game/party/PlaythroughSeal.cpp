#include "game/party/PlaythroughSeal.h"

#include "PlaythroughStatisticsKey.h"

#include <monocypher.h>

#include <algorithm>
#include <array>
#include <random>

#if OPENYAMM_HAS_RELEASE_STATS_KEY
namespace OpenYAMM::Game::PlaythroughSealRelease
{
// Defined by the private release key source (cmake/PlaythroughStatisticsKey.cmake), which is not in the repository:
// writes the 32-byte release key to pKey and returns its version label.
const char *assembleKey(uint8_t *pKey);
}
#endif

namespace OpenYAMM::Game::PlaythroughSeal
{
namespace
{
// "OYSEAL" and the format version.
constexpr std::array<char, 8> Magic = {'O', 'Y', 'S', 'E', 'A', 'L', '0', '1'};
constexpr size_t NonceSize = 24;
constexpr size_t MacSize = 16;
constexpr char DevelopmentKeyVersion[] = "dev";

using Key = std::array<uint8_t, 32>;

// The development key is public: anyone may build the game, and its records say they came from such a build.
constexpr Key DevelopmentKey = {
    0x4f, 0x70, 0x65, 0x6e, 0x59, 0x41, 0x4d, 0x4d, 0x2d, 0x64, 0x65, 0x76, 0x2d, 0x73, 0x74, 0x61,
    0x74, 0x69, 0x73, 0x74, 0x69, 0x63, 0x73, 0x2d, 0x6b, 0x65, 0x79, 0x2d, 0x30, 0x30, 0x30, 0x31};

#if OPENYAMM_HAS_RELEASE_STATS_KEY
Key releaseKey(std::string *pVersion = nullptr)
{
    Key key = {};
    const char *pKeyVersion = PlaythroughSealRelease::assembleKey(key.data());

    if (pVersion != nullptr)
    {
        *pVersion = pKeyVersion != nullptr ? pKeyVersion : "";
    }

    return key;
}

const std::string &releaseKeyVersion()
{
    static const std::string version = []()
    {
        std::string label;
        Key key = releaseKey(&label);
        crypto_wipe(key.data(), key.size());
        return label;
    }();
    return version;
}
#endif

std::optional<Key> keyFor(const std::string &keyVersion)
{
    if (keyVersion == DevelopmentKeyVersion)
    {
        return DevelopmentKey;
    }

#if OPENYAMM_HAS_RELEASE_STATS_KEY
    if (!releaseKeyVersion().empty() && keyVersion == releaseKeyVersion())
    {
        return releaseKey();
    }
#endif

    return std::nullopt;
}

struct Header
{
    Kind kind = Kind::Lifetime;
    std::string keyVersion;
    std::string playthroughId;
    // Where the nonce starts: everything before it is the authenticated header.
    size_t headerSize = 0;
};

std::string encodeHeader(Kind kind, const std::string &keyVersion, const std::string &playthroughId)
{
    std::string header(Magic.begin(), Magic.end());
    header.push_back(char(kind));
    header.push_back(char(uint8_t(keyVersion.size())));
    header += keyVersion;
    header.push_back(char(uint8_t(playthroughId.size() & 0xff)));
    header.push_back(char(uint8_t((playthroughId.size() >> 8) & 0xff)));
    header += playthroughId;
    return header;
}

std::optional<Header> decodeHeader(const std::string &bytes)
{
    if (!looksSealed(bytes) || bytes.size() < Magic.size() + 2)
    {
        return std::nullopt;
    }

    Header header;
    size_t offset = Magic.size();
    header.kind = Kind(uint8_t(bytes[offset++]));
    const size_t versionSize = uint8_t(bytes[offset++]);

    if (offset + versionSize + 2 > bytes.size())
    {
        return std::nullopt;
    }

    header.keyVersion = bytes.substr(offset, versionSize);
    offset += versionSize;
    const size_t idSize = size_t(uint8_t(bytes[offset])) | (size_t(uint8_t(bytes[offset + 1])) << 8);
    offset += 2;

    if (offset + idSize + NonceSize + MacSize > bytes.size())
    {
        return std::nullopt;
    }

    header.playthroughId = bytes.substr(offset, idSize);
    header.headerSize = offset + idSize;
    return header;
}
}

const std::string &sealingKeyVersion()
{
#if OPENYAMM_HAS_RELEASE_STATS_KEY
    return releaseKeyVersion();
#else
    static const std::string version = DevelopmentKeyVersion;
    return version;
#endif
}

bool sealsWithReleaseKey()
{
    return OPENYAMM_HAS_RELEASE_STATS_KEY != 0;
}

std::string seal(Kind kind, const std::string &playthroughId, const std::string &text)
{
    std::optional<Key> key = keyFor(sealingKeyVersion());
    std::string sealed = encodeHeader(kind, sealingKeyVersion(), playthroughId);
    const size_t headerSize = sealed.size();

    // A fresh random nonce per seal; XChaCha20's 24 bytes make repeats negligible.
    std::array<uint8_t, NonceSize> nonce = {};
    std::random_device device;

    for (size_t index = 0; index < nonce.size(); index += 4)
    {
        const uint32_t value = device();

        for (size_t part = 0; part < 4 && index + part < nonce.size(); ++part)
        {
            nonce[index + part] = uint8_t(value >> (8 * part));
        }
    }

    sealed.append(reinterpret_cast<const char *>(nonce.data()), nonce.size());
    sealed.append(MacSize, '\0');
    sealed.append(text.size(), '\0');
    uint8_t *pMac = reinterpret_cast<uint8_t *>(sealed.data()) + headerSize + NonceSize;
    uint8_t *pCipherText = pMac + MacSize;
    crypto_aead_lock(pCipherText, pMac, key->data(), nonce.data(),
        reinterpret_cast<const uint8_t *>(sealed.data()), headerSize,
        reinterpret_cast<const uint8_t *>(text.data()), text.size());
    crypto_wipe(key->data(), key->size());
    return sealed;
}

std::optional<Opened> open(Kind kind, const std::string &playthroughId, const std::string &sealed)
{
    const std::optional<Header> header = decodeHeader(sealed);

    if (!header || header->kind != kind || header->playthroughId != playthroughId)
    {
        return std::nullopt;
    }

    std::optional<Key> key = keyFor(header->keyVersion);

    if (!key)
    {
        return std::nullopt;
    }

    const uint8_t *pBytes = reinterpret_cast<const uint8_t *>(sealed.data());
    const uint8_t *pNonce = pBytes + header->headerSize;
    const uint8_t *pMac = pNonce + NonceSize;
    const uint8_t *pCipherText = pMac + MacSize;
    const size_t textSize = sealed.size() - header->headerSize - NonceSize - MacSize;
    Opened opened;
    opened.text.resize(textSize);
    const int failed = crypto_aead_unlock(reinterpret_cast<uint8_t *>(opened.text.data()), pMac, key->data(), pNonce,
        pBytes, header->headerSize, pCipherText, textSize);
    crypto_wipe(key->data(), key->size());

    if (failed != 0)
    {
        return std::nullopt;
    }

    opened.keyVersion = header->keyVersion;
    opened.developmentKey = header->keyVersion == DevelopmentKeyVersion;
    return opened;
}

bool looksSealed(const std::string &bytes)
{
    return bytes.size() >= Magic.size() && std::equal(Magic.begin(), Magic.end(), bytes.begin());
}

std::string keyVersionOf(const std::string &sealed)
{
    const std::optional<Header> header = decodeHeader(sealed);
    return header ? header->keyVersion : std::string();
}

bool knowsKey(const std::string &keyVersion)
{
    std::optional<Key> key = keyFor(keyVersion);

    if (!key)
    {
        return false;
    }

    crypto_wipe(key->data(), key->size());
    return true;
}
}
