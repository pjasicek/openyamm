#pragma once

// The idle scan of a stationary turret (worlds/<id>/behaviors.yml tactics `scan`, ActorTacticsFacts::scan). With no
// target the turret sweeps left and right around its placement facing: each move eases in and out (smoothstep, so a
// turnaround never snaps), ends at a random heading, alternates sides (ping-pong) or now and then stops part-way, and
// is followed by a short random pause; some moves also change the barrel's pitch a little. Every turret draws its own
// random sequence (seeded by its actor id) and starts after its own delay, so a wall of turrets never moves in step.
// ActorBehaviorRuntime keeps one state per turret (not saved) and gives the AI the resulting facing each step.

#include <algorithm>
#include <cmath>
#include <cstdint>

namespace OpenYAMM::Game
{
struct TurretScanSettings
{
    // The sweep, radians either side of the scan's centre (the placement facing).
    float halfWidthRadians = 0.0f;
    // The peak turn rate of a sweep (radians per second); 0 disables the scan.
    float radiansPerSecond = 0.0f;
    // The pause after each move, uniformly in this range.
    float pauseMinSeconds = 0.0f;
    float pauseMaxSeconds = 0.0f;
    // The barrel pitch (presentation) wanders within this either side of level.
    float pitchRadians = 0.0f;
    // After losing its target the turret holds its last aim this long, then eases back into the scan.
    float holdSeconds = 0.0f;

    bool enabled() const
    {
        return radiansPerSecond > 0.0f;
    }
};

struct TurretScanPose
{
    float yawOffsetRadians = 0.0f;
    float pitchRadians = 0.0f;
};

struct TurretScanState
{
    uint32_t random = 1;
    float fromYaw = 0.0f;
    float toYaw = 0.0f;
    float fromPitch = 0.0f;
    float toPitch = 0.0f;
    float moveSeconds = 0.0f;
    float pauseSeconds = 0.0f;
    float elapsedSeconds = 0.0f;
    // The side (+1 left, -1 right) the next full sweep ends on.
    float sweepSide = 1.0f;
    // A move that starts outside the sweep (back from a fight) turns at least at this rate.
    float returnRadiansPerSecond = 0.0f;
};

inline float turretScanRandom(TurretScanState &state)
{
    // xorshift32: deterministic per turret, so tests and replays see the same scan.
    uint32_t value = state.random;
    value ^= value << 13;
    value ^= value >> 17;
    value ^= value << 5;
    state.random = value;
    return float(value >> 8) * (1.0f / 16777216.0f);
}

inline float turretScanEase(float t)
{
    const float clamped = std::clamp(t, 0.0f, 1.0f);
    return clamped * clamped * (3.0f - 2.0f * clamped);
}

// The next move from the end of the current one.
inline void beginTurretScanMove(TurretScanState &state, const TurretScanSettings &settings)
{
    const float width = std::max(0.0f, settings.halfWidthRadians);
    const float from = state.toYaw;
    state.fromYaw = from;
    state.fromPitch = state.toPitch;
    float speed = settings.radiansPerSecond;

    if (std::abs(from) > width * 1.05f)
    {
        // Outside the sweep (it turned to a target): back to the near edge of the sweep, at the return rate.
        state.sweepSide = from > 0.0f ? 1.0f : -1.0f;
        state.toYaw = state.sweepSide * width * (0.6f + 0.4f * turretScanRandom(state));
        state.sweepSide = -state.sweepSide;
        speed = std::max(speed, state.returnRadiansPerSecond);
    }
    else
    {
        const float sweepEnd = state.sweepSide * width * (0.55f + 0.45f * turretScanRandom(state));

        if (turretScanRandom(state) < 0.25f && std::abs(sweepEnd - from) > 0.5f * width)
        {
            // A stop part-way along the sweep; the sweep goes on to the same side afterwards.
            state.toYaw = from + (sweepEnd - from) * (0.35f + 0.3f * turretScanRandom(state));
        }
        else
        {
            state.toYaw = sweepEnd;
            state.sweepSide = -state.sweepSide;
        }
    }

    if (turretScanRandom(state) < 0.6f)
    {
        state.toPitch = settings.pitchRadians * (2.0f * turretScanRandom(state) - 1.0f);
    }

    // Smoothstep peaks at 1.5 times its mean rate: the duration that keeps the peak at `speed`.
    const float distance = std::abs(state.toYaw - state.fromYaw);
    state.moveSeconds = speed > 0.0f ? std::max(0.6f, 1.5f * distance / speed) : 0.6f;
    const float pauseMin = std::max(0.0f, settings.pauseMinSeconds);
    const float pauseMax = std::max(pauseMin, settings.pauseMaxSeconds);
    state.pauseSeconds = pauseMin + (pauseMax - pauseMin) * turretScanRandom(state);
    state.elapsedSeconds = 0.0f;
}

// Starts (or restarts) the scan from the turret's current offset from the centre and the scan pitch it shows. It
// first stands still for delaySeconds; a start outside the sweep returns at least at returnRadiansPerSecond.
inline void startTurretScan(TurretScanState &state, uint32_t seed, float currentYawOffset, float currentPitch,
    float delaySeconds, float returnRadiansPerSecond)
{
    state = {};
    state.random = (seed * 2654435761u) ^ 0x9e3779b9u;

    if (state.random == 0)
    {
        state.random = 1;
    }

    turretScanRandom(state);
    state.fromYaw = currentYawOffset;
    state.toYaw = currentYawOffset;
    state.fromPitch = currentPitch;
    state.toPitch = currentPitch;
    state.sweepSide = currentYawOffset > 0.01f ? -1.0f
        : currentYawOffset < -0.01f ? 1.0f
        : turretScanRandom(state) < 0.5f ? -1.0f : 1.0f;
    state.returnRadiansPerSecond = std::max(0.0f, returnRadiansPerSecond);
    state.moveSeconds = 0.0f;
    state.pauseSeconds = std::max(0.0f, delaySeconds);
}

inline TurretScanPose turretScanPose(const TurretScanState &state)
{
    const float t = state.moveSeconds > 0.0f ? turretScanEase(state.elapsedSeconds / state.moveSeconds) : 1.0f;
    return {state.fromYaw + (state.toYaw - state.fromYaw) * t, state.fromPitch + (state.toPitch - state.fromPitch) * t};
}

inline TurretScanPose advanceTurretScan(TurretScanState &state, const TurretScanSettings &settings, float deltaSeconds)
{
    state.elapsedSeconds += std::max(0.0f, deltaSeconds);

    // A long step (a map's first frame) may cross several moves; the bound only guards degenerate settings.
    for (int move = 0; move < 64 && state.elapsedSeconds >= state.moveSeconds + state.pauseSeconds; ++move)
    {
        const float carried = state.elapsedSeconds - state.moveSeconds - state.pauseSeconds;
        beginTurretScanMove(state, settings);
        state.elapsedSeconds = carried;
    }

    return turretScanPose(state);
}
}
