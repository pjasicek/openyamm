#pragma once

#include "engine/AssetPackIndex.h"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Engine
{
// The updater's manifest format (packaging/UPDATER_PLAN.md 7.1), written by packaging/publish_release.py.
inline constexpr uint32_t ReleaseManifestSchema = 1;
// Bumped when the updater changes in a way a newer manifest can require (min_updater_schema).
inline constexpr uint32_t UpdaterSchema = 1;

// A file in the update store, addressed relative to the channel's base URL (updates/) or by an absolute https URL.
struct ReleaseFile
{
    std::string file;
    std::string url;
    uint64_t size = 0;
    std::string sha256;
};

struct ReleaseManifest
{
    std::string channel;
    std::string platform;
    std::string release;
    std::string build;
    std::string published;
    std::string notesUrl;
    // Short release notes for the update question (optional).
    std::string notes;
    uint32_t contentFormat = 0;
    uint32_t minUpdaterSchema = 0;
    ReleaseFile app;
    std::optional<int64_t> androidVersionCode;
    // The pack records of the release's index; each pack is at packUrls[i]. The languages' optional packs (listed
    // apart in a desktop manifest, under language_packs) follow the others.
    std::vector<AssetPackRecord> packs;
    std::vector<std::string> packUrls;
};

std::optional<ReleaseManifest> parseReleaseManifest(const std::string &text, std::string &error);

// The manifest public keys compiled into the game (packaging/keys/manifest-ed25519-<slot>.pub): slot 1 signs
// releases, slot 2 is the offline rotation key.
struct ManifestPublicKey
{
    int slot = 0;
    std::array<uint8_t, 32> key = {};
};
const std::vector<ManifestPublicKey> &releaseManifestPublicKeys();

// Checks <platform>.json.sig ({"key": slot, "algorithm": "ed25519", "signature": base64}) over the exact manifest
// bytes. Returns the slot that verified.
std::optional<int> verifyManifestSignature(const std::string &manifestBytes, const std::string &signatureJson,
                                           const std::vector<ManifestPublicKey> &keys, std::string &error);

// Orders canonical X.Y release names numerically; nullopt when either is not one (development and test builds).
std::optional<int> compareReleaseVersions(const std::string &left, const std::string &right);
}
