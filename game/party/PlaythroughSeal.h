#pragma once

#include <cstdint>
#include <optional>
#include <string>

namespace OpenYAMM::Game
{
// Sealed playthrough statistics (devdocs/PLAYTHROUGH_STATISTICS_PLAN.md, "Sealed files"): the YAML text encrypted and
// authenticated with XChaCha20-Poly1305 (Monocypher's crypto_aead_lock). The header (format, key version, playthrough
// id and which copy) is authenticated too, so neither the text nor the header can be edited, and a timeline cannot be
// passed off as a lifetime or as another playthrough's.
//
// A release build seals with the release key built in from outside the repository (cmake/PlaythroughStatisticsKey.cmake)
// and also opens what development builds sealed with the built-in development key; a development build opens only its
// own. The key in the executable can be found by anyone who works at it: this keeps out casual editing, nothing more.
namespace PlaythroughSeal
{
enum class Kind : uint8_t
{
    Lifetime = 1,
    Timeline = 2,
};

struct Opened
{
    std::string text;
    std::string keyVersion;
    // Sealed with the development key (a build without the release key).
    bool developmentKey = false;
};

// The key version this build seals with: the release key's ("release-1"), else "dev".
const std::string &sealingKeyVersion();
bool sealsWithReleaseKey();

std::string seal(Kind kind, const std::string &playthroughId, const std::string &text);
// Nothing when the bytes are not a sealed record of this kind and playthrough, were changed, or need a key this build
// does not have.
std::optional<Opened> open(Kind kind, const std::string &playthroughId, const std::string &sealed);
// The bytes start like a sealed record (whatever its key): an unopenable one is not plain text either.
bool looksSealed(const std::string &bytes);
// The key version a sealed record names, or empty.
std::string keyVersionOf(const std::string &sealed);
// This build has the key of that version (a development build lacks the release key).
bool knowsKey(const std::string &keyVersion);
}
}
