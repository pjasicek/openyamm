#pragma once

#include <bx/math.h>

#include <cstddef>
#include <cstdint>
#include <functional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
class GameplayScreenRuntime;
struct GameplayCombatFeedbackEvent;

// The damage numbers over struck monsters, shared by the indoor and outdoor views. Every number has one ivory-gold
// colour and one size; a critical hit pops (it swells, settles larger than a plain hit, holds, then rises and fades)
// and a hit a raised energy shield took whole is shield blue. The numbers on one monster never pile up: the newest
// starts at the monster and pushes the older ones up above it, so a whole party's volley reads as a column.
class CombatFloatingText
{
public:
    // Maps a world point to screen pixels; false when it is behind the camera.
    using ProjectWorldPoint = std::function<bool(const bx::Vec3 &, float &, float &)>;

    static void preload(const GameplayScreenRuntime &screenRuntime);

    void clear();
    // Ages the numbers and adds one for each hit in `events` on an actor below `actorCount`; with `enabled` off
    // (the combat text setting) it keeps none.
    void update(float deltaSeconds, const std::vector<GameplayCombatFeedbackEvent> &events, size_t actorCount,
        bool enabled);
    void render(const GameplayScreenRuntime &screenRuntime, int width, int height,
        const ProjectWorldPoint &project) const;

private:
    struct Entry
    {
        size_t actorIndex = 0;
        std::string text;
        bx::Vec3 origin = {0.0f, 0.0f, 0.0f};
        // Its centre's height above the origin's screen point, in plain number cells: its own rise, or higher when
        // newer numbers on the same monster need the room below it. Eased, so a pushed number glides up.
        float liftCells = 0.0f;
        float ageSeconds = 0.0f;
        float durationSeconds = 0.0f;
        uint32_t colorAbgr = 0xffffffffu;
        bool critical = false;
    };

    std::vector<Entry> m_entries;
};
}
