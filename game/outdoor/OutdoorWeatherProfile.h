#pragma once

#include <array>
#include <cstdint>

namespace OpenYAMM::Game
{
enum class OutdoorFogMode : uint8_t
{
    Static = 0,
    DailyRandom = 1,
};

enum class OutdoorPrecipitationKind : uint8_t
{
    None = 0,
    Snow = 1,
    Rain = 2,
};

struct OutdoorFogDistances
{
    int32_t weakDistance = 0;
    int32_t strongDistance = 0;
};

struct OutdoorWeatherProfile
{
    OutdoorFogMode fogMode = OutdoorFogMode::Static;
    OutdoorPrecipitationKind defaultPrecipitation = OutdoorPrecipitationKind::None;
    bool alwaysFoggy = false;
    bool redFog = false;
    bool hasFogTint = false;
    std::array<uint8_t, 3> fogTintRgb = {255, 255, 255};
    bool underwater = false;
    OutdoorFogDistances defaultFog = {};
    int smallFogChance = 0;
    int averageFogChance = 0;
    int denseFogChance = 0;
    OutdoorFogDistances smallFog = {4096, 8192};
    OutdoorFogDistances averageFog = {0, 4096};
    OutdoorFogDistances denseFog = {0, 2048};
};
}
