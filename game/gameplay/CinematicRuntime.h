#pragma once

#include "game/gameplay/GameplayRuntimeInterfaces.h"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace OpenYAMM::Game
{
// In-engine cinematics (devdocs/mm9_rework/MM9_CUTSCENES.md): a map's <stem>.cinematics.yml names cinematics, each
// a sequence of camera shots and a list of timed cues (fades, sounds, subtitles, map events, actor steps, camera
// shake). Lua starts one with evt.PlayCinematic(id[, doneEventId]); while it plays the camera is the cinematic's, the
// party takes no input and the gameplay HUD is hidden; Escape, Space or Return skips a skippable one. Shared by every
// world, indoors and outdoors; never saved (a save waits until the cinematic has ended).

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
    FadeOut,        // to black over seconds
    FadeIn,         // from black over seconds
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

// What the cinematic needs from the world (GameSession adapts the active world runtime; tests fake it).
class ICinematicWorld
{
public:
    virtual ~ICinematicWorld() = default;

    // The actor's feet and body height; nullopt for no such actor.
    virtual std::optional<GameplayWorldPoint> actorFeet(size_t actorIndex) const = 0;
    virtual float actorHeight(size_t actorIndex) const = 0;
    virtual GameplayWorldPoint partyEye() const = 0;
    virtual void runEvent(uint16_t eventId) = 0;
    virtual void playSound(const std::string &soundName) = 0;
    virtual void setActorHidden(size_t actorIndex, bool hidden) = 0;
    virtual void placeActor(size_t actorIndex, const GameplayWorldPoint &feet) = 0;
    // Presentation (EventRuntimeState::actorPresentations): a heading the actor turns to over seconds, a clip it plays
    // once or looping, and both cleared (its own animation and facing again).
    virtual void faceActor(size_t actorIndex, float yawRadians, float seconds) = 0;
    virtual void playActorClip(size_t actorIndex, const std::string &clip, bool loop) = 0;
    virtual void clearActorPresentation(size_t actorIndex) = 0;
    // A decoration model (by its cog: EventRuntimeState::decorationAims) glides to an offset over seconds.
    virtual void moveDecoration(uint32_t decorationKey, const GameplayWorldPoint &offset, float seconds) = 0;
};

struct EventRuntimeState;

// Gives a map actor's presented state the clip and facing of its EventRuntimeState::actorPresentations entry (the
// worlds' actorRuntimeState, after their own clips: a cinematic's wins). Nothing for a dead actor.
void applyActorPresentation(const EventRuntimeState *pEvents, size_t actorIndex, GameplayRuntimeActorState &state);

struct CinematicCameraView
{
    GameplayWorldPoint eye = {};
    float yawRadians = 0.0f;
    float pitchRadians = 0.0f;
    std::optional<float> verticalFovDegrees;
};

// Camera shake (evt.CameraShake and the cinematics' shake cues): a smooth tremor of the view's yaw and pitch that
// fades out over its seconds. Several shakes add up. Transient, never saved.
class CameraShake
{
public:
    // intensity 1 is a strong quake (about one degree); 0 or less does nothing.
    void start(float intensity, float seconds);
    void update(float deltaSeconds);
    void clear();
    bool active() const;
    float yawRadians() const;
    float pitchRadians() const;

private:
    struct Entry
    {
        float intensity = 0.0f;
        float seconds = 0.0f;
        float elapsedSeconds = 0.0f;
        float phase = 0.0f;
    };

    std::vector<Entry> m_entries;
    float m_yawRadians = 0.0f;
    float m_pitchRadians = 0.0f;
    uint32_t m_startCount = 0;
};

class CinematicRuntime
{
public:
    // Starts the cinematic (a copy is kept); a playing one is skipped first. doneEventId 0: none.
    void start(const CinematicDefinition &definition, uint16_t doneEventId, ICinematicWorld &world);
    // Advances it by deltaSeconds: due cues run, then the camera follows. The update after the one that reached its
    // end finishes it (that frame still draws it) and runs the done event.
    void update(float deltaSeconds, ICinematicWorld &world);
    // Ends it: the remaining map events run now in order, actors take their final places, presentation cues (sounds,
    // subtitles, fades, shakes) are dropped; the next update finishes it and runs the done event. Does nothing for an
    // unskippable one unless forced.
    bool skip(ICinematicWorld &world, bool force = false);
    // Drops it without running anything (the map changed).
    void stop();

    bool active() const;
    bool skippable() const;
    // A playing cinematic that takes over the view (camera, input, HUD): every one but an ambient one.
    bool takesOverView() const;
    const std::string &activeId() const;
    float elapsedSeconds() const;
    // The shot playing (its index), nullopt when the party's own view shows.
    std::optional<size_t> activeShotIndex() const;

    // The camera this frame, nullopt when the party's view shows.
    const std::optional<CinematicCameraView> &cameraView() const;
    // Black bars, 0 none to 1 full (bars that leave a 2:1 picture); black over the screen, 0 to 1.
    float letterboxAmount() const;
    float fadeAmount() const;
    const std::string &subtitle() const;

    CameraShake &shake();
    const CameraShake &shake() const;

private:
    struct ActorMove
    {
        size_t actorIndex = 0;
        GameplayWorldPoint from = {};
        GameplayWorldPoint to = {};
        float startSeconds = 0.0f;
        float seconds = 0.0f;
    };

    void runCue(const CinematicCue &cue, ICinematicWorld &world);
    void advanceMoves(ICinematicWorld &world);
    void updatePresentation();
    void updateCamera(const ICinematicWorld &world);
    void finish(ICinematicWorld &world);

    std::optional<CinematicDefinition> m_definition;
    uint16_t m_doneEventId = 0;
    bool m_ending = false;
    float m_elapsedSeconds = 0.0f;
    size_t m_nextCue = 0;
    std::vector<ActorMove> m_moves;
    // Actors whose presentation it set (cleared at its end) and the decorations it moved (their last offsets: a skip
    // puts them there at once).
    std::vector<size_t> m_presentedActors;
    std::vector<std::pair<uint32_t, GameplayWorldPoint>> m_movedDecorations;

    float m_fadeFrom = 0.0f;
    float m_fadeTo = 0.0f;
    float m_fadeStartSeconds = 0.0f;
    float m_fadeSeconds = 0.0f;
    float m_fadeAmount = 0.0f;
    float m_letterboxFrom = 0.0f;
    float m_letterboxTo = 0.0f;
    float m_letterboxStartSeconds = 0.0f;
    float m_letterboxSeconds = 0.0f;
    float m_letterboxAmount = 0.0f;
    std::string m_subtitle;
    float m_subtitleEndSeconds = 0.0f;

    std::optional<size_t> m_shotIndex;
    std::optional<CinematicCameraView> m_cameraView;
    CameraShake m_shake;
};
}
