// S6 (devdocs/map_studio/S6_PLAN.md): the Cinematics panel's timeline and camera (items C) and the Overlay panel's
// grouping and frame (item O).
import { describe, expect, it } from 'vitest';
import { cameraAt, cueKind, readCinematics, timelineOf } from './cinematics.ts';
import type { Cinematic, Point3 } from './cinematics.ts';
import { overlayFrame, summariseOverlay } from './overlay.ts';
import type { ViewOverlayResult } from '../../../schema/rpc/generated/rpc.ts';

// The S6 test map's arrival (examples/s6_breakwater/wiring.yml).
const arrival: Cinematic = {
    id: 'cinematic:arrival',
    shots: [
        { seconds: 2.5, at: [120, 120, 420], look_at: 'deco:barrel', fov: 70 },
        { seconds: 3, at: [800, 300, 200], look_at: [1120, 384, 128], easing: 'smooth',
            keys: [{ seconds: 3, at: [960, 384, 180], look_at: [1120, 384, 128] }] },
        { seconds: 1, party: true },
    ],
    cues: [
        { at: 0, fade: 'in', seconds: 1 },
        { at: 2.5, subtitle: 'The store is barred from within.', seconds: 2.5 },
        { at: 3, event: 'evt:arrival_lamp' },
        { at: 5, shake: 0.3, seconds: 1 },
    ],
};
const places: Record<string, Point3> = { 'deco:barrel': [880, 880, 0] };
const resolve = (place: Point3 | string): Point3 | null => (typeof place === 'string' ? places[place] ?? null : place);

describe('cinematics', () =>
{
    it('reads the cinematics of a wiring.yml tree and nothing else', () =>
    {
        expect(readCinematics({ format: 0, cinematics: [arrival, { id: 'x' }, 3] })).toEqual([arrival]);
        expect(readCinematics({ format: 0 })).toEqual([]);
        expect(readCinematics(null)).toEqual([]);
    });

    it('lays the shots back to back and the cues at their seconds; the length is the later end', () =>
    {
        const timeline = timelineOf(arrival);
        expect(timeline.shots.map((shot) => [shot.start, shot.end])).toEqual([[0, 2.5], [2.5, 5.5], [5.5, 6.5]]);
        expect(timeline.shots[1]!.moving).toBe(true);
        expect(timeline.shots[2]!.party).toBe(true);
        expect(timeline.cues.map((cue) => cue.kind)).toEqual(['fade', 'subtitle', 'event', 'shake']);
        expect(timeline.cues[0]!.end).toBe(1);
        expect(timeline.cues[2]!.end).toBe(3);
        // The game's 6.5 s (its log: "arrival starts (6.5 s)").
        expect(timeline.length).toBe(6.5);
        // A cue past the shots makes it longer.
        expect(timelineOf({ ...arrival, cues: [{ at: 7, subtitle: 'x', seconds: 2 }] }).length).toBe(9);
        expect(cueKind({ at: 0, monster: 'monster:boss', action: 'hide' })).toBe('monster');
    });

    it('puts the camera where the game does: a fixed shot, a moving one eased by smoothstep, the party view', () =>
    {
        const fixed = cameraAt(arrival, 1, resolve)!;
        expect(fixed.shot).toBe(0);
        expect(fixed.position).toEqual([120, 120, 420]);
        expect(fixed.target).toEqual([880, 880, 0]);
        // Half way through the moving shot: smoothstep(0.5) = 0.5.
        const middle = cameraAt(arrival, 4, resolve)!;
        expect(middle.shot).toBe(1);
        expect(middle.position).toEqual([880, 342, 190]);
        // A quarter of the way: smoothstep(0.25) = 0.15625.
        const quarter = cameraAt(arrival, 3.25, resolve)!;
        expect(quarter.position[0]).toBeCloseTo(800 + 160 * 0.15625, 6);
        // Linear easing moves evenly.
        const linear = cameraAt({ ...arrival, shots: [{ ...arrival.shots[1]!, easing: 'linear' }] }, 0.75, resolve)!;
        expect(linear.position[0]).toBeCloseTo(840, 6);
        expect(cameraAt(arrival, 6, resolve)!.party).toBe(true);
        expect(cameraAt(arrival, 7, resolve)).toBeNull();
        // A yaw and pitch aim: a point ahead.
        const turned = cameraAt({ id: 'c', shots: [{ seconds: 1, at: [0, 0, 0], yaw: 90, pitch: 0 }] }, 0, resolve)!;
        expect(turned.target![1]).toBeCloseTo(1000, 6);
        // A place that names nothing.
        expect(cameraAt({ id: 'c', shots: [{ seconds: 1, at: 'deco:none', look_at: [0, 0, 0] }] }, 0, resolve)).toBeNull();
    });
});

describe('overlay', () =>
{
    const result: ViewOverlayResult = {
        base: 'isleofashes.blv', world: 'mm9', profile: 'region', bounds: [-32512, -32512, 32512, 32512],
        scene_keys: ['pulsing_lights', 'destructibles'], issues: [],
        things: [
            { id: 'light:beacon', kind: 'light', origin: 'added', state: 'added', at: [1400, 4800, 1000], radius: 1200, label: 'pulsing light 49001' },
            { id: 'destructible:k520', kind: 'destructible', origin: 'base', state: 'changed', at: [-655, 5407, 471], label: 'FortWall' },
            { id: 'spawn:s6', kind: 'spawn', origin: 'base', state: 'removed', at: [1824, 1696, 815], radius: 32, label: 'item roll 1' },
            { id: 'sound:a1', kind: 'sound', origin: 'base', state: 'kept', at: [0, 0, 0], radius: 900, label: 'x.wav' },
            { id: 'sound:a2', kind: 'sound', origin: 'base', state: 'kept', at: [5, 0, 0], radius: 900, label: 'y.wav' },
        ],
    };

    it('groups the things by what the project does, its own first, and counts the base map\'s', () =>
    {
        const summary = summariseOverlay(result);
        expect(summary.groups.map((group) => group.state)).toEqual(['added', 'changed', 'removed', 'kept']);
        expect(summary.changes).toBe(3);
        expect(summary.baseByKind).toEqual({ destructible: 1, spawn: 1, sound: 2 });
    });

    it('frames what the project touches, or the whole map when it touches nothing', () =>
    {
        const frame = overlayFrame(result);
        expect(frame[0]).toBeLessThan(-655);
        expect(frame[2]).toBeGreaterThan(1400 + 1200);
        expect(frame[2] - frame[0]).toBeLessThan(20000);
        expect(overlayFrame({ ...result, things: result.things.filter((thing) => thing.state === 'kept') }))
            .toEqual([-32512, -32512, 32512, 32512]);
    });
});
