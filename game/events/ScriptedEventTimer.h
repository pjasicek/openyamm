#pragma once

#include <cstdint>
#include <functional>
#include <vector>

namespace OpenYAMM::Game
{
enum class ScriptedEventScope : uint8_t
{
    Map,
    Global,
};

enum class ScriptedEventTimerOrigin : uint8_t
{
    Native,
    Legacy,
};

enum class ScriptedEventTimerTriggerKind : uint8_t
{
    None,
    Timer,
    LongTimer,
};

enum class ScriptedEventTimerScheduleKind : uint8_t
{
    Relative,
    Interval,
    Daily,
    Weekly,
    Monthly,
    Yearly,
};

struct ScriptedEventTimerDefinition
{
    ScriptedEventScope scope = ScriptedEventScope::Map;
    ScriptedEventTimerOrigin origin = ScriptedEventTimerOrigin::Native;
    ScriptedEventTimerTriggerKind triggerKind = ScriptedEventTimerTriggerKind::None;
    ScriptedEventTimerScheduleKind scheduleKind = ScriptedEventTimerScheduleKind::Relative;
    uint16_t eventId = 0;
    uint16_t sourceEventId = 0;
    uint8_t triggerStep = 0;
    uint32_t registrationIndex = 0;
    bool repeating = false;
    uint16_t intervalHalfMinutes = 0;
    int startHour = 0;
    int startMinute = 0;
    int startSecond = 0;
    double intervalGameMinutes = 0.0;
    double initialDelayGameMinutes = 0.0;
};

struct ScriptedEventTimerState
{
    ScriptedEventTimerDefinition definition;
    double nextAlarmGameMinutes = 0.0;
    double eligibleGameMinutes = 0.0;
    bool hasFired = false;
    bool initialCalendarFirePending = false;
    bool migratedFromLegacySave = false;
    double migratedRemainingGameMinutes = 0.0;
    // Stopped by evt.StopTimer until evt.StartTimer; saved with the map's timers.
    bool stopped = false;
};

double legacyTimerGameMinutesFromTicks(int64_t legacyTicks);
int64_t legacyTimerTicksFromGameMinutes(double gameMinutes);

bool sameScriptedEventTimerIdentity(
    const ScriptedEventTimerDefinition &left,
    const ScriptedEventTimerDefinition &right);

std::vector<ScriptedEventTimerState> reconcileScriptedEventTimers(
    const std::vector<ScriptedEventTimerState> &savedStates,
    const std::vector<ScriptedEventTimerDefinition> &definitions,
    double currentGameMinutes,
    int64_t lastVisitTime,
    bool resetLegacyTimers);

// evt.StopTimer / evt.StartTimer on the timers of an event: stop them, or run them again with their next alarm
// delayGameMinutes from now (negative: one interval; a one-shot timer may fire again).
void controlScriptedEventTimers(
    std::vector<ScriptedEventTimerState> &states,
    uint16_t eventId,
    bool start,
    double delayGameMinutes,
    double currentGameMinutes);

// An evt.StopTimer / evt.StartTimer request, queued by the script and applied by updateScriptedEventTimers.
struct ScriptedEventTimerControl
{
    uint16_t eventId = 0;
    bool start = false;
    double delayGameMinutes = -1.0;
};

// Fire the due timers. With pControls, first apply and clear the requests queued since the last update, then those
// each handler queues as soon as it returns. A request a timer's handler makes on its own event counts its delay
// from the alarm that ran the handler, not from the frame that did, so a handler that restarts itself keeps its
// period instead of adding a frame each time (from the current time when that alarm lies more than the delay
// behind: time skipped by rest or a stall).
bool updateScriptedEventTimers(
    std::vector<ScriptedEventTimerState> &states,
    double currentGameMinutes,
    const std::function<bool(const ScriptedEventTimerDefinition &)> &executeTimer,
    std::vector<ScriptedEventTimerControl> *pControls = nullptr);
}
