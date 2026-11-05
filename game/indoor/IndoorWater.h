#pragma once

#include "game/indoor/IndoorFog.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
struct IndoorVertex;

// MM9's deep water (devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md, MM9_WATER_SWIMMING_RE.md): water volumes the party
// swims and dives in, with breath and drowning. Opt-in per map through the scene's `water_volumes`; a map without them
// (every MM6-MM8 map) runs none of this. Everything here is pure: map data in, numbers out.

enum class IndoorLiquid : uint8_t
{
    Water = 0,
    Lava,
};

// A vertical prism: a horizontal footprint and its z range (native units). MM9's water brushes all have flat tops.
struct IndoorWaterPiece
{
    std::vector<std::array<float, 2>> polygon;
    float bottom = 0.0f;
    float top = 0.0f;
    // The footprint's bounds, minX, minY, maxX, maxY (finalizeIndoorWaterPiece).
    std::array<float, 4> bounds = {0.0f, 0.0f, 0.0f, 0.0f};
};

struct IndoorWaterVolume
{
    std::string id;
    IndoorLiquid liquid = IndoorLiquid::Water;
    std::vector<IndoorWaterPiece> pieces;
    // MM9's light scale while the eye is inside (cshell 0x100ab8a0): BlueWater (0, 0.5, 0.7) by default.
    std::array<float, 3> tint = {0.0f, 0.5f, 0.7f};
    // The volume's own fog while the eye is inside (MM9 FogEnable); disabled: the map's fog.
    IndoorFog fog;
    // Added to the velocity of a body in the water, native units per second (MM9 Current).
    std::array<float, 3> current = {0.0f, 0.0f, 0.0f};
    // A door whose travel moves every piece's top (MM9's DrainWater.scr volumes); its first vertex is followed.
    std::optional<uint32_t> moverDoorId;
    std::optional<uint16_t> moverVertexId;
};

// MM9's light scale of a liquid class: water BlueWater's, lava Kato's.
std::array<float, 3> indoorLiquidDefaultTint(IndoorLiquid liquid);
// Fills the piece's bounds from its polygon.
void finalizeIndoorWaterPiece(IndoorWaterPiece &piece);
bool indoorWaterPieceContains(const IndoorWaterPiece &piece, float x, float y);

struct IndoorWaterSample
{
    size_t volumeIndex = 0;
    float surfaceZ = 0.0f;
    float bottomZ = 0.0f;
};

// Each volume's top offset now: a mover-bound volume's door vertex height against its stored height (zero for every
// other volume). `runtimeVertices` are the map's vertices with the doors where they stand now.
std::vector<float> indoorWaterTopOffsets(
    std::span<const IndoorWaterVolume> volumes,
    std::span<const IndoorVertex> storedVertices,
    std::span<const IndoorVertex> runtimeVertices);

// The water the point is in (bottom <= z < top; topOffsets may be empty).
std::optional<IndoorWaterSample> indoorWaterAt(
    std::span<const IndoorWaterVolume> volumes,
    std::span<const float> topOffsets,
    float x,
    float y,
    float z);
// The water a vertical body column [footZ, footZ + height] at (x, y) reaches into: the highest surface of the pieces
// over (x, y) it overlaps.
std::optional<IndoorWaterSample> indoorBodyWaterSample(
    std::span<const IndoorWaterVolume> volumes,
    std::span<const float> topOffsets,
    float x,
    float y,
    float footZ,
    float height);
// The piece of one volume over (x, y), its sample (for a body bound to the volume).
std::optional<IndoorWaterSample> indoorWaterVolumeColumn(
    std::span<const IndoorWaterVolume> volumes,
    std::span<const float> topOffsets,
    size_t volumeIndex,
    float x,
    float y);

// MM9's numbers (x 2.56 native units per LT).
inline constexpr float IndoorSwimSpeed = 384.0f;              // Swim Vel 150 LT/s, = walking; running keeps it
inline constexpr float IndoorSwimIdleSinkSpeed = 102.4f;      // liquid gravity -200 LT/s^2 x 0.2
inline constexpr float IndoorSwimEyePointDrop = 25.6f;        // the head test: 10 LT under the top of the body
inline constexpr float IndoorSwimSurfaceHold = 1.0f;          // the surface pose: the eye point this far over the water
inline constexpr float IndoorSurfaceJumpVelocity = 704.0f;    // jump vel 275 LT/s
inline constexpr float IndoorSurfaceJumpForwardSpeed = 384.0f;    // air control 150 LT/s forward
inline constexpr float IndoorSurfaceJumpSideSpeed = 192.0f;       // 75 LT/s back and sideways
inline constexpr float IndoorBreathSeconds = 15.0f;
inline constexpr float IndoorDrowningTickSeconds = 2.0f;
inline constexpr int IndoorDrowningMaxHealthDivisor = 6;       // each tick takes 1/6 of each member's maximum HP
// Monsters: MM9 multiplies a walker's velocity by 1 - Viscosity (0.5 in every DAT) and replaces its gravity by the
// liquid's -200 LT/s^2.
inline constexpr float IndoorWaterWalkerSpeedFactor = 0.5f;
inline constexpr float IndoorWaterWalkerGravity = 512.0f;

// The party's water state, derived each movement step from geometry plus two remembered bits, as MM9 derives its
// mover each frame (cshell 0x10099270).
enum class IndoorSwimState : uint8_t
{
    Dry = 0,        // the body touches no water
    Wading,         // feet on a floor, body in water, eye out: walking
    Falling,        // airborne, body in water, the eye not yet under since it entered: today's fall
    Bed,            // feet on a floor with the eye under water: walking on the bed (MM9 WalkingInWater)
    Submerged,      // the eye under water, off the floor: swimming
    Surface,        // eye out, body in, having been under: held at the surface
    SurfaceJump,    // the jump out of the water from the surface
};

const char *indoorSwimStateName(IndoorSwimState state);

struct IndoorSwimMemory
{
    bool wasSubmerged = false;
    bool surfaceJump = false;
};

struct IndoorSwimFacts
{
    bool bodyInWater = false;
    bool eyeUnder = false;
    bool grounded = false;
};

// The state for these facts; updates the remembered bits (MM9 0x10099339..0x100993ab): the eye under sets "was
// submerged" and ends a surface jump; a body out of all water clears both; landing ends a surface jump.
IndoorSwimState indoorSwimState(const IndoorSwimFacts &facts, IndoorSwimMemory &memory);

struct IndoorSwimInput
{
    // -1..1: Forward minus Backward, StepRight minus StepLeft; vertical: Jump or Fly Up +1, Fly Down -1.
    float forward = 0.0f;
    float strafe = 0.0f;
    int vertical = 0;
    float yawRadians = 0.0f;
    float pitchRadians = 0.0f;
    // The input's own speed share (an analog stick) and the turbo key.
    float speedScale = 1.0f;
};

struct IndoorSwimVelocity
{
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
};

// The swimming velocity of a Submerged or Surface body (MM9 UnderWater 0x100953b0, SwimmingOnSurface 0x10095880):
// set from the input each step, no momentum. Under water forward follows the look direction with its pitch, strafe the
// camera's right, vertical the world's up, the sum clamped to the swim speed (MM9 adds them unclamped); with no input
// at all it sinks. On the surface the look direction cannot rise and nothing sinks; `eyePointOverSurface` (the eye
// point's height over the water) is pulled to the surface pose.
IndoorSwimVelocity indoorSwimVelocity(
    IndoorSwimState state,
    const IndoorSwimInput &input,
    float speedMultiplier,
    float eyePointOverSurface,
    float deltaSeconds);
// The horizontal air control of the surface jump (MM9 SwimmingJump 0x10095c50): forward 384, back and sideways 192.
IndoorSwimVelocity indoorSurfaceJumpAirControl(const IndoorSwimInput &input, float speedMultiplier);

// Breath (MM9 object.lto 0x100c3d20, 0x100c5560): 15 s with the eye under water, then a drowning tick every 2 s; out
// of the water it refills at once.
struct IndoorBreathState
{
    float underSeconds = 0.0f;
    float nextTickSeconds = IndoorBreathSeconds;
};

// Advances the breath; returns the drowning ticks due.
uint32_t advanceIndoorBreath(IndoorBreathState &breath, bool eyeUnder, float deltaSeconds);
// 1 full, 0 out of breath.
float indoorBreathFraction(const IndoorBreathState &breath);
// The damage of one drowning tick to a member (at least 1).
int indoorDrowningDamage(int maxHealth);
}
