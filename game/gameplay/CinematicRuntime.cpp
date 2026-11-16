#include "game/gameplay/CinematicRuntime.h"
#include "engine/Localization.h"

#include "game/events/EventRuntime.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <utility>

namespace OpenYAMM::Game
{
namespace
{
constexpr float MaxPitchRadians = 1.55f;
// Where the camera looks on an actor: three quarters of its height (about the face of a standing figure).
constexpr float ActorAimHeightFraction = 0.75f;
// CameraShake: radians of yaw (pitch: two thirds of it) at intensity 1, at the start of a shake.
constexpr float ShakeRadiansPerIntensity = 0.018f;

GameplayWorldPoint lerp(const GameplayWorldPoint &from, const GameplayWorldPoint &to, float t)
{
    return {from.x + (to.x - from.x) * t, from.y + (to.y - from.y) * t, from.z + (to.z - from.z) * t};
}

std::optional<GameplayWorldPoint> normalized(const GameplayWorldPoint &vector)
{
    const float length = std::sqrt(vector.x * vector.x + vector.y * vector.y + vector.z * vector.z);

    if (length < 1.0e-4f)
    {
        return std::nullopt;
    }

    return GameplayWorldPoint{vector.x / length, vector.y / length, vector.z / length};
}

// The spline's velocity at a key (units per second): the neighbours' difference over their time span; zero at the
// first and last key and at a key with the same value as a neighbour (a hold).
GameplayWorldPoint splineTangent(const std::vector<GameplayWorldPoint> &values, const std::vector<float> &times,
    size_t index)
{
    const auto same = [&](size_t left, size_t right)
    {
        const GameplayWorldPoint &a = values[left];
        const GameplayWorldPoint &b = values[right];
        return std::abs(a.x - b.x) + std::abs(a.y - b.y) + std::abs(a.z - b.z) < 1.0e-3f;
    };

    if (index == 0 || index + 1 >= values.size() || same(index, index - 1) || same(index, index + 1)
        || times[index + 1] <= times[index - 1])
    {
        return {};
    }

    const float span = times[index + 1] - times[index - 1];
    const GameplayWorldPoint &next = values[index + 1];
    const GameplayWorldPoint &previous = values[index - 1];
    return {(next.x - previous.x) / span, (next.y - previous.y) / span, (next.z - previous.z) / span};
}

// The cubic Hermite between keys from and from + 1 at t (0..1 of the segment).
GameplayWorldPoint splineAt(const std::vector<GameplayWorldPoint> &values, const std::vector<float> &times,
    size_t from, float t)
{
    const size_t to = from + 1;
    const float duration = times[to] - times[from];
    const GameplayWorldPoint startTangent = splineTangent(values, times, from);
    const GameplayWorldPoint endTangent = splineTangent(values, times, to);
    const float t2 = t * t;
    const float t3 = t2 * t;
    const float h00 = 2.0f * t3 - 3.0f * t2 + 1.0f;
    const float h10 = (t3 - 2.0f * t2 + t) * duration;
    const float h01 = -2.0f * t3 + 3.0f * t2;
    const float h11 = (t3 - t2) * duration;
    const GameplayWorldPoint &p0 = values[from];
    const GameplayWorldPoint &p1 = values[to];
    return {h00 * p0.x + h10 * startTangent.x + h01 * p1.x + h11 * endTangent.x,
        h00 * p0.y + h10 * startTangent.y + h01 * p1.y + h11 * endTangent.y,
        h00 * p0.z + h10 * startTangent.z + h01 * p1.z + h11 * endTangent.z};
}

std::optional<GameplayWorldPoint> keyDirection(
    const CinematicCameraKey &key,
    const GameplayWorldPoint &eye,
    const ICinematicWorld &world)
{
    std::optional<GameplayWorldPoint> target;

    switch (key.aim)
    {
        case CinematicAim::Direction:
            return key.aimVector;
        case CinematicAim::Point:
            target = key.aimVector;
            break;
        case CinematicAim::Party:
            target = world.partyEye();
            break;
        case CinematicAim::Actor:
            if (const std::optional<GameplayWorldPoint> feet = world.actorFeet(key.actorIndex))
            {
                target = GameplayWorldPoint{feet->x, feet->y,
                    feet->z + world.actorHeight(key.actorIndex) * ActorAimHeightFraction};
            }
            break;
    }

    return target ? normalized({target->x - eye.x, target->y - eye.y, target->z - eye.z}) : std::nullopt;
}
}

void applyActorPresentation(const EventRuntimeState *pEvents, size_t actorIndex, GameplayRuntimeActorState &state)
{
    if (pEvents == nullptr || pEvents->actorPresentations.empty() || state.isDead)
    {
        return;
    }

    const auto found = pEvents->actorPresentations.find(uint32_t(actorIndex));

    if (found == pEvents->actorPresentations.end())
    {
        return;
    }

    const EventRuntimeState::ActorPresentation &presentation = found->second;

    if (!presentation.clip.empty())
    {
        state.scriptedClip = presentation.clip;
        state.scriptedClipThen = presentation.then;
        state.scriptedClipSeconds = presentation.clipSeconds;
        state.scriptedClipEnd = presentation.hold ? GameplayRuntimeActorState::ScriptedClipEnd::Hold
            : presentation.loop ? GameplayRuntimeActorState::ScriptedClipEnd::Loop
            : GameplayRuntimeActorState::ScriptedClipEnd::Release;
    }

    if (presentation.yawRadians)
    {
        state.yawRadians = *presentation.yawRadians;
    }
}


void CameraShake::start(float intensity, float seconds)
{
    if (!(intensity > 0.0f) || !(seconds > 0.0f))
    {
        return;
    }

    Entry entry = {};
    entry.intensity = std::min(intensity, 10.0f);
    entry.seconds = std::min(seconds, MaxCinematicSeconds);
    // Each shake starts at its own phase, so two at once do not move in step.
    entry.phase = float(m_startCount++) * 2.399963f;
    m_entries.push_back(entry);
}

void CameraShake::update(float deltaSeconds)
{
    m_yawRadians = 0.0f;
    m_pitchRadians = 0.0f;

    for (Entry &entry : m_entries)
    {
        entry.elapsedSeconds += std::max(deltaSeconds, 0.0f);
    }

    std::erase_if(m_entries, [](const Entry &entry) { return entry.elapsedSeconds >= entry.seconds; });

    for (const Entry &entry : m_entries)
    {
        // Fades out over its seconds (quadratically: most of the shaking is early, as a quake's jolt).
        const float remaining = 1.0f - entry.elapsedSeconds / entry.seconds;
        const float amplitude = entry.intensity * ShakeRadiansPerIntensity * remaining * remaining;
        const float t = entry.elapsedSeconds;
        m_yawRadians += amplitude * (0.6f * std::sin(t * 71.0f + entry.phase) + 0.4f * std::sin(t * 117.0f
            + entry.phase * 1.7f));
        m_pitchRadians += amplitude * 0.67f * (0.6f * std::sin(t * 89.0f + entry.phase * 0.6f)
            + 0.4f * std::sin(t * 53.0f + entry.phase * 2.3f));
    }
}

void CameraShake::clear()
{
    m_entries.clear();
    m_yawRadians = 0.0f;
    m_pitchRadians = 0.0f;
}

bool CameraShake::active() const
{
    return !m_entries.empty();
}

float CameraShake::yawRadians() const
{
    return m_yawRadians;
}

float CameraShake::pitchRadians() const
{
    return m_pitchRadians;
}

void CinematicRuntime::start(const CinematicDefinition &definition, uint16_t doneEventId, ICinematicWorld &world)
{
    if (active())
    {
        skip(world, true);
        finish(world);
    }

    m_definition = definition;
    m_doneEventId = doneEventId;
    m_elapsedSeconds = 0.0f;
    m_nextCue = 0;
    m_ending = false;
    m_moves.clear();
    m_fadeFrom = m_fadeTo = m_fadeAmount = 0.0f;
    m_fadeSeconds = 0.0f;
    m_letterboxFrom = m_letterboxTo = m_letterboxAmount = 0.0f;
    m_letterboxSeconds = 0.0f;
    m_subtitle.clear();
    m_cameraView.reset();
    m_shotIndex.reset();
    update(0.0f, world);
}

void CinematicRuntime::update(float deltaSeconds, ICinematicWorld &world)
{
    if (!m_definition)
    {
        return;
    }

    // The last frame showed its end (or a skip): it finishes now, so that frame still drew the cinematic (a map move
    // its last event asks for happens after that frame, with no party view between).
    if (m_ending)
    {
        finish(world);
        return;
    }

    m_elapsedSeconds += std::max(deltaSeconds, 0.0f);

    while (m_definition && m_nextCue < m_definition->cues.size()
        && m_definition->cues[m_nextCue].atSeconds <= m_elapsedSeconds)
    {
        runCue(m_definition->cues[m_nextCue++], world);
    }

    if (!m_definition)
    {
        return;
    }

    advanceMoves(world);
    updatePresentation();
    updateCamera(world);

    m_ending = m_elapsedSeconds >= m_definition->durationSeconds && m_nextCue >= m_definition->cues.size();
}

bool CinematicRuntime::skip(ICinematicWorld &world, bool force)
{
    if (!m_definition || (!m_definition->skippable && !force))
    {
        return false;
    }

    // The rest of the cinematic happens at once: its map events in order, its actors at their last places.
    for (const ActorMove &move : m_moves)
    {
        world.placeActor(move.actorIndex, move.to);
    }

    m_moves.clear();

    while (m_definition && m_nextCue < m_definition->cues.size())
    {
        const CinematicCue &cue = m_definition->cues[m_nextCue++];

        switch (cue.kind)
        {
            case CinematicCueKind::Event:
            case CinematicCueKind::ActorShow:
            case CinematicCueKind::ActorHide:
            case CinematicCueKind::ActorPlace:
                runCue(cue, world);
                break;
            case CinematicCueKind::ActorMove:
                world.placeActor(cue.actorIndex, cue.point);
                break;
            case CinematicCueKind::DecorationMove:
                m_movedDecorations.emplace_back(cue.decorationKey, cue.point);
                break;
            default:
                break;
        }
    }

    // Decorations at their last offsets now (a glide still under way included).
    for (const auto &[key, offset] : m_movedDecorations)
    {
        world.moveDecoration(key, offset, 0.0f);
    }

    m_movedDecorations.clear();

    m_subtitle.clear();
    m_ending = true;
    return true;
}

void CinematicRuntime::stop()
{
    m_definition.reset();
    m_ending = false;
    m_presentedActors.clear();
    m_movedDecorations.clear();
    m_doneEventId = 0;
    m_elapsedSeconds = 0.0f;
    m_nextCue = 0;
    m_moves.clear();
    m_fadeAmount = 0.0f;
    m_letterboxAmount = 0.0f;
    m_subtitle.clear();
    m_cameraView.reset();
    m_shotIndex.reset();
}

bool CinematicRuntime::active() const
{
    return m_definition.has_value();
}

bool CinematicRuntime::skippable() const
{
    return m_definition && m_definition->skippable;
}

bool CinematicRuntime::takesOverView() const
{
    return m_definition && !m_definition->ambient;
}

const std::string &CinematicRuntime::activeId() const
{
    static const std::string None;
    return m_definition ? m_definition->id : None;
}

float CinematicRuntime::elapsedSeconds() const
{
    return m_elapsedSeconds;
}

std::optional<size_t> CinematicRuntime::activeShotIndex() const
{
    return m_cameraView ? m_shotIndex : std::nullopt;
}

const std::optional<CinematicCameraView> &CinematicRuntime::cameraView() const
{
    return m_cameraView;
}

float CinematicRuntime::letterboxAmount() const
{
    return m_letterboxAmount;
}

float CinematicRuntime::fadeAmount() const
{
    return m_fadeAmount;
}

const std::string &CinematicRuntime::subtitle() const
{
    return m_subtitle;
}

CameraShake &CinematicRuntime::shake()
{
    return m_shake;
}

const CameraShake &CinematicRuntime::shake() const
{
    return m_shake;
}

void CinematicRuntime::runCue(const CinematicCue &cue, ICinematicWorld &world)
{
    switch (cue.kind)
    {
        case CinematicCueKind::FadeOut:
        case CinematicCueKind::FadeIn:
            m_fadeFrom = cue.kind == CinematicCueKind::FadeOut ? m_fadeAmount : 1.0f;
            m_fadeTo = cue.kind == CinematicCueKind::FadeOut ? 1.0f : 0.0f;
            m_fadeStartSeconds = cue.atSeconds;
            m_fadeSeconds = cue.seconds;
            break;
        case CinematicCueKind::Letterbox:
            m_letterboxFrom = m_letterboxAmount;
            m_letterboxTo = cue.amount;
            m_letterboxStartSeconds = cue.atSeconds;
            m_letterboxSeconds = cue.seconds;
            break;
        case CinematicCueKind::Sound:
            world.playSound(cue.text);
            break;
        case CinematicCueKind::Subtitle:
            m_subtitle = Engine::localize(cue.text);
            m_subtitleEndSeconds = cue.atSeconds + cue.seconds;
            break;
        case CinematicCueKind::Event:
            world.runEvent(cue.eventId);
            break;
        case CinematicCueKind::ActorShow:
        case CinematicCueKind::ActorHide:
            world.setActorHidden(cue.actorIndex, cue.kind == CinematicCueKind::ActorHide);
            break;
        case CinematicCueKind::ActorPlace:
            std::erase_if(m_moves, [&](const ActorMove &move) { return move.actorIndex == cue.actorIndex; });
            world.placeActor(cue.actorIndex, cue.point);
            break;
        case CinematicCueKind::ActorMove:
            if (const std::optional<GameplayWorldPoint> feet = world.actorFeet(cue.actorIndex))
            {
                std::erase_if(m_moves, [&](const ActorMove &move) { return move.actorIndex == cue.actorIndex; });
                m_moves.push_back({cue.actorIndex, *feet, cue.point, cue.atSeconds, cue.seconds});
            }
            break;
        case CinematicCueKind::ActorFace:
            if (const std::optional<GameplayWorldPoint> feet = world.actorFeet(cue.actorIndex))
            {
                std::optional<GameplayWorldPoint> target;

                if (cue.aim == CinematicAim::Point)
                {
                    target = cue.point;
                }
                else if (cue.aim == CinematicAim::Party)
                {
                    target = world.partyEye();
                }
                else
                {
                    target = world.actorFeet(cue.aimActorIndex);
                }

                if (target && (std::abs(target->x - feet->x) > 0.01f || std::abs(target->y - feet->y) > 0.01f))
                {
                    world.faceActor(cue.actorIndex, std::atan2(target->y - feet->y, target->x - feet->x), cue.seconds);
                    m_presentedActors.push_back(cue.actorIndex);
                }
            }
            break;
        case CinematicCueKind::ActorClip:
            world.playActorClip(cue.actorIndex, cue.text, cue.loop);
            m_presentedActors.push_back(cue.actorIndex);
            break;
        case CinematicCueKind::DecorationMove:
            world.moveDecoration(cue.decorationKey, cue.point, cue.seconds);
            m_movedDecorations.emplace_back(cue.decorationKey, cue.point);
            break;
        case CinematicCueKind::Shake:
            m_shake.start(cue.amount, cue.seconds);
            break;
    }
}

void CinematicRuntime::advanceMoves(ICinematicWorld &world)
{
    for (const ActorMove &move : m_moves)
    {
        const float t = std::clamp((m_elapsedSeconds - move.startSeconds) / move.seconds, 0.0f, 1.0f);
        world.placeActor(move.actorIndex, lerp(move.from, move.to, t));
    }

    std::erase_if(m_moves,
        [&](const ActorMove &move) { return m_elapsedSeconds >= move.startSeconds + move.seconds; });
}

void CinematicRuntime::updatePresentation()
{
    const auto ramp =
        [&](float from, float to, float startSeconds, float seconds)
        {
            const float t = seconds > 0.0f ? std::clamp((m_elapsedSeconds - startSeconds) / seconds, 0.0f, 1.0f) : 1.0f;
            return from + (to - from) * t;
        };

    m_fadeAmount = ramp(m_fadeFrom, m_fadeTo, m_fadeStartSeconds, m_fadeSeconds);
    m_letterboxAmount = ramp(m_letterboxFrom, m_letterboxTo, m_letterboxStartSeconds, m_letterboxSeconds);

    if (!m_subtitle.empty() && m_elapsedSeconds >= m_subtitleEndSeconds)
    {
        m_subtitle.clear();
    }
}

void CinematicRuntime::updateCamera(const ICinematicWorld &world)
{
    float shotStart = 0.0f;
    const CinematicShot *pShot = nullptr;

    for (size_t index = 0; index < m_definition->shots.size(); ++index)
    {
        const CinematicShot &shot = m_definition->shots[index];

        if (m_elapsedSeconds < shotStart + shot.durationSeconds)
        {
            pShot = &shot;
            m_shotIndex = index;
            break;
        }

        shotStart += shot.durationSeconds;
    }

    if (pShot == nullptr || pShot->keys.empty())
    {
        m_cameraView.reset();
        return;
    }

    const float local = m_elapsedSeconds - shotStart;
    size_t from = 0;

    while (from + 1 < pShot->keys.size() && pShot->keys[from + 1].atSeconds <= local)
    {
        ++from;
    }

    const size_t to = std::min(from + 1, pShot->keys.size() - 1);
    const CinematicCameraKey &fromKey = pShot->keys[from];
    const CinematicCameraKey &toKey = pShot->keys[to];
    float t = to == from ? 0.0f
        : std::clamp((local - fromKey.atSeconds) / (toKey.atSeconds - fromKey.atSeconds), 0.0f, 1.0f);

    if (pShot->easing == CinematicEasing::Smooth)
    {
        t = t * t * (3.0f - 2.0f * t);
    }

    CinematicCameraView view = {};
    view.eye = lerp(fromKey.position, toKey.position, t);
    std::vector<float> times;
    const bool spline = pShot->easing == CinematicEasing::Spline && to != from;

    if (spline)
    {
        std::vector<GameplayWorldPoint> positions;

        for (const CinematicCameraKey &key : pShot->keys)
        {
            times.push_back(key.atSeconds);
            positions.push_back(key.position);
        }

        view.eye = splineAt(positions, times, from, t);
    }

    const std::optional<GameplayWorldPoint> fromDirection = keyDirection(fromKey, view.eye, world);
    const std::optional<GameplayWorldPoint> toDirection = keyDirection(toKey, view.eye, world);
    std::optional<GameplayWorldPoint> direction;

    if (fromDirection && toDirection)
    {
        direction = normalized(lerp(*fromDirection, *toDirection, t));
    }

    if (spline && fromDirection && toDirection)
    {
        // The aims along the same curve, each key's direction seen from the current eye.
        std::vector<GameplayWorldPoint> directions;

        for (const CinematicCameraKey &key : pShot->keys)
        {
            const std::optional<GameplayWorldPoint> keyAim = keyDirection(key, view.eye, world);
            directions.push_back(keyAim ? *keyAim : *fromDirection);
        }

        direction = normalized(splineAt(directions, times, from, t));
    }

    direction = direction ? direction : (t < 0.5f ? fromDirection : toDirection);

    if (!direction && m_cameraView)
    {
        // The aim is gone (an actor removed): keep the last view's direction.
        view.yawRadians = m_cameraView->yawRadians;
        view.pitchRadians = m_cameraView->pitchRadians;
    }
    else if (direction)
    {
        view.yawRadians = std::atan2(direction->y, direction->x);
        view.pitchRadians = std::clamp(std::asin(std::clamp(direction->z, -1.0f, 1.0f)), -MaxPitchRadians,
            MaxPitchRadians);
    }

    if (fromKey.verticalFovDegrees && toKey.verticalFovDegrees)
    {
        view.verticalFovDegrees = *fromKey.verticalFovDegrees
            + (*toKey.verticalFovDegrees - *fromKey.verticalFovDegrees) * t;
    }
    else
    {
        view.verticalFovDegrees = fromKey.verticalFovDegrees ? fromKey.verticalFovDegrees : toKey.verticalFovDegrees;
    }

    m_cameraView = view;
}

void CinematicRuntime::finish(ICinematicWorld &world)
{
    const uint16_t doneEventId = m_doneEventId;
    // Its actors return to their own animation and facing.
    std::sort(m_presentedActors.begin(), m_presentedActors.end());
    m_presentedActors.erase(std::unique(m_presentedActors.begin(), m_presentedActors.end()), m_presentedActors.end());

    for (const size_t actorIndex : m_presentedActors)
    {
        world.clearActorPresentation(actorIndex);
    }

    stop();

    if (doneEventId != 0)
    {
        world.runEvent(doneEventId);
    }
}
}
