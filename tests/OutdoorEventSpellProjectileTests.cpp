#include <doctest/doctest.h>

#include "engine/AssetFileSystem.h"
#include "game/data/GameDataLoader.h"
#include "game/outdoor/OutdoorWorldRuntime.h"
#include "game/party/SkillData.h"
#include "game/party/SpellIds.h"
#include "game/ui/GameplayOverlayTypes.h"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <limits>

using namespace OpenYAMM::Game;

TEST_CASE("emerald island cannon death blossom leaves its collision box and bursts out at sea")
{
    OpenYAMM::Engine::AssetFileSystem assets;
    const std::filesystem::path sourceRoot = OPENYAMM_SOURCE_DIR;
    REQUIRE(assets.initialize(sourceRoot, sourceRoot / "assets_dev", OpenYAMM::Engine::AssetScaleTier::X1, "mm7"));
    GameDataLoader data;
    REQUIRE(data.loadForHeadlessGameplay(assets));
    REQUIRE(data.loadMapByFileNameForHeadlessGameplay(assets, "7out01.odm"));
    const MapAssetInfo &loaded = *data.getSelectedMap();
    REQUIRE(loaded.outdoorMapData);

    OutdoorWorldRuntime world;
    world.initialize(loaded.map, data.getMonsterTable(), data.getMonsterProjectileTable(), data.getObjectTable(),
        data.getSpellTable(), data.getItemTable(), nullptr, nullptr, data.getStandardItemEnchantTable(),
        data.getSpecialItemEnchantTable(), &data.getChestTable(), loaded.outdoorMapData,
        std::nullopt, std::nullopt, std::nullopt);

    // Event 219 (the cannon's button): CastSpell Death Blossom, GM 10, from the muzzle, which lies inside the
    // invisible B0x_W blocker box around the cannon, towards the sea.
    constexpr float CannonX = 10495.0f;
    constexpr float CannonY = 17724.0f;
    constexpr float CannonZ = 2370.0f;
    REQUIRE(world.castEventSpell(
        spellIdValue(SpellId::DeathBlossom),
        10,
        static_cast<uint32_t>(SkillMastery::Grandmaster),
        10495,
        17724,
        2370,
        10495,
        24144,
        4500));
    REQUIRE(world.projectileCount() == 1);

    const OutdoorWorldRuntime::ProjectileState *pBlossom = world.projectileState(0);
    REQUIRE(pBlossom != nullptr);
    const float horizontalSpeed = std::hypot(pBlossom->velocityX, pBlossom->velocityY);
    CHECK(pBlossom->velocityY > 0.0f);
    CHECK(pBlossom->velocityZ == doctest::Approx(horizontalSpeed).epsilon(0.01));

    // The party stands at the button behind the cannon.
    constexpr float PartyX = 10495.0f;
    constexpr float PartyY = 17440.0f;
    constexpr float PartyZ = 2144.0f;
    float nearestShardDistance = std::numeric_limits<float>::max();
    bool sawShard = false;

    for (int step = 0; step < 1280; ++step)
    {
        world.updateMapActors(1.0f / 128.0f, PartyX, PartyY, PartyZ);

        if (step == 32)
        {
            // A quarter second in, the blossom is still flying, well past the box wall at y = 17768.
            pBlossom = nullptr;

            for (size_t projectileIndex = 0; projectileIndex < world.projectileCount(); ++projectileIndex)
            {
                const OutdoorWorldRuntime::ProjectileState *pProjectile = world.projectileState(projectileIndex);

                if (pProjectile != nullptr
                    && pProjectile->spellId == static_cast<int>(spellIdValue(SpellId::DeathBlossom))
                    && pProjectile->objectName != "shard")
                {
                    pBlossom = pProjectile;
                }
            }

            REQUIRE(pBlossom != nullptr);
            CHECK(pBlossom->y > 17768.0f + 200.0f);
            CHECK(pBlossom->z > CannonZ + 200.0f);
            CHECK(world.projectileImpactCount() == 0);
        }

        for (size_t projectileIndex = 0; projectileIndex < world.projectileCount(); ++projectileIndex)
        {
            const OutdoorWorldRuntime::ProjectileState *pProjectile = world.projectileState(projectileIndex);

            if (pProjectile != nullptr && pProjectile->objectName == "shard")
            {
                sawShard = true;
                nearestShardDistance = std::min(
                    nearestShardDistance,
                    std::hypot(pProjectile->x - CannonX, pProjectile->y - CannonY));
            }
        }
    }

    // The blossom bursts out at sea and no fallout shard comes within area-damage reach of the cannon.
    CHECK(sawShard);
    CHECK(nearestShardDistance > 1200.0f);
}
