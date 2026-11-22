#pragma once

#include "game/gameplay/GameplayWorldPoint.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// The format of a map's <stem>.cinematics.yml (devdocs/mm9_rework/MM9_CUTSCENES.md) and its parser, apart from the
// runtime that plays it (CinematicRuntime.h), so that tools read the file with the game's own rules. Needs nothing
// of the event or gameplay runtime.

// The longest cinematic, shot or cue time the format takes (seconds).
constexpr float MaxCinematicSeconds = 3600.0f;

enum class CinematicAim : uint8_t
{
    Point,      // look at a fixed point
    Actor,      // look at a map actor's centre, following it
    Party,      // look at the party's eye
    Direction,  // look along a fixed direction
};

struct CinematicCameraKey
{
    float atSeconds = 0.0f;                 // from the start of its shot
    GameplayWorldPoint position = {};
    CinematicAim aim = CinematicAim::Direction;
    GameplayWorldPoint aimVector = {1.0f, 0.0f, 0.0f};  // the point (Point) or the unit direction (Direction)
    size_t actorIndex = 0;
    std::optional<float> verticalFovDegrees;
};

enum class CinematicEasing : uint8_t
{
    Linear,
    Smooth,     // smoothstep between keys
    // One curve through all the keys (Catmull-Rom by their times): the camera glides through them at a continuous
    // speed, at rest at the first and last key and at a key repeated (a hold).
    Spline,
};

struct CinematicShot
{
    float durationSeconds = 0.0f;
    // One key: a fixed camera. Several: the camera moves through them (position eased, direction blended).
    // None: the party's own view (party: true).
    std::vector<CinematicCameraKey> keys;
    CinematicEasing easing = CinematicEasing::Smooth;
};

enum class CinematicCueKind : uint8_t
{
    FadeOut,        // to its colour (colorRgb, black by default) over seconds
    FadeIn,         // from its colour over seconds
    Letterbox,      // bars on (amount 1) or off (0) over seconds
    Sound,          // text: a sound name as evt.PlaySoundName takes it
    Subtitle,       // text, shown for seconds
    Event,          // runs a map event (also when skipped)
    ActorShow,
    ActorHide,
    ActorPlace,     // point: the actor's feet
    ActorMove,      // to point over seconds, in a straight line
    ActorFace,      // turns to its aim over seconds (0: at once)
    ActorClip,      // text: a clip (an actors.yml script_clips role or the model's clip name), once or looping
    DecorationMove, // decorationKey glides to point (an offset from its map position) over seconds; the glide goes
                    // on past the cinematic's end (it does not lengthen it)
    Shake,          // amount: intensity, over seconds
};

struct CinematicCue
{
    float atSeconds = 0.0f;
    CinematicCueKind kind = CinematicCueKind::Event;
    float seconds = 0.0f;
    float amount = 0.0f;
    std::string text;
    uint16_t eventId = 0;
    size_t actorIndex = 0;
    GameplayWorldPoint point = {};
    // ActorFace: what it turns to (Point: point, Actor: aimActorIndex, Party).
    CinematicAim aim = CinematicAim::Point;
    size_t aimActorIndex = 0;
    bool loop = false;
    uint32_t decorationKey = 0;
    // FadeOut, FadeIn: the colour of the veil (D-56's fade to white); black by default.
    std::array<uint8_t, 3> colorRgb = {0, 0, 0};
};

struct CinematicDefinition
{
    std::string id;
    bool skippable = true;
    bool letterbox = true;
    // Overheard talk (MM9's first-sight banter): no camera, no letterbox, no input lock; the HUD stays and the
    // subtitles show over it. Its cues play as any cinematic's; no shots.
    bool ambient = false;
    float letterboxSeconds = 0.5f;
    std::vector<CinematicShot> shots;
    std::vector<CinematicCue> cues;      // sorted by time, stable
    float durationSeconds = 0.0f;        // the later of the shots' end and the last cue's end
};

struct CinematicLibrary
{
    std::vector<CinematicDefinition> cinematics;

    const CinematicDefinition *find(const std::string &id) const;
};

// Parses a .cinematics.yml text. Unknown keys, missing fields and out-of-range values are errors naming the
// cinematic and the shot or cue.
std::optional<CinematicLibrary> parseCinematicLibrary(const std::string &yamlText, std::string &error);

// A cinematics overlay (`<stem>_<name>.cinematics.yml`) over the library read so far: a cinematic of an id the
// library has replaces it in its place; a new id is added at the end.
void mergeCinematicLibrary(CinematicLibrary &library, CinematicLibrary &&overlay);
}
