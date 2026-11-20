// wiring.yml `cinematics` (devdocs/map_studio/S6_PLAN.md item C) for the Cinematics panel: the timeline (shots one
// after another, cues at their seconds, each lasting what the game makes it last) and the camera at a moment, as the
// game's runtime moves it (game/gameplay/CinematicRuntime.cpp: a moving shot's keys eased by smoothstep or linearly; a
// spline shot is shown as smooth here). Places that name objects are resolved by the caller (the layout's things).

export type Point3 = [number, number, number];

export interface CinematicKey
{
    seconds?: number;
    at?: Point3 | string;
    offset?: Point3;
    look_at?: Point3 | string;
    yaw?: number;
    pitch?: number;
}

export interface CinematicShot extends CinematicKey
{
    seconds: number;
    party?: boolean;
    fov?: number;
    easing?: 'smooth' | 'linear' | 'spline';
    keys?: CinematicKey[];
}

export interface CinematicCue
{
    at: number;
    seconds?: number;
    event?: string;
    sound?: string;
    subtitle?: string;
    fade?: 'in' | 'out';
    letterbox?: boolean;
    shake?: number;
    monster?: string;
    action?: string;
}

export interface Cinematic
{
    id: string;
    skippable?: boolean;
    letterbox?: boolean;
    shots: CinematicShot[];
    cues?: CinematicCue[];
}

export interface TimelineShot
{
    index: number;
    start: number;
    end: number;
    label: string;
    moving: boolean;
    party: boolean;
}

export interface TimelineCue
{
    index: number;
    start: number;
    end: number;
    kind: string;
    label: string;
}

export interface Timeline
{
    length: number;
    shots: TimelineShot[];
    cues: TimelineCue[];
}

const isRecord = (value: unknown): value is Record<string, unknown> => value !== null && typeof value === 'object'
    && !Array.isArray(value);

// The cinematics of a wiring.yml tree (the project's own file as project.open gives it).
export function readCinematics(tree: unknown): Cinematic[]
{
    if (!isRecord(tree) || !Array.isArray(tree.cinematics))
    {
        return [];
    }

    return tree.cinematics.filter((entry): entry is Cinematic => isRecord(entry) && typeof entry.id === 'string'
        && Array.isArray(entry.shots));
}

const CUE_KINDS = ['event', 'sound', 'subtitle', 'fade', 'letterbox', 'shake', 'monster'] as const;

export function cueKind(cue: CinematicCue): string
{
    return CUE_KINDS.find((kind) => cue[kind] !== undefined) ?? 'cue';
}

function describePlace(place: Point3 | string | undefined): string
{
    if (place === undefined)
    {
        return '';
    }

    return typeof place === 'string' ? place : `[${place.map((value) => Math.round(value)).join(', ')}]`;
}

// Shots back to back; a cue lasts its seconds (a fade 1 by default, a sound and an event a moment); the cinematic as
// long as the later of its last shot and its last cue (MM9_CUTSCENES.md section 3).
export function timelineOf(cinematic: Cinematic): Timeline
{
    let time = 0;
    const shots: TimelineShot[] = cinematic.shots.map((shot, index) =>
    {
        const start = time;
        time += Math.max(0, shot.seconds ?? 0);
        const moving = Array.isArray(shot.keys) && shot.keys.length > 0;
        const label = shot.party ? 'party view'
            : `${describePlace(shot.at)}${shot.look_at !== undefined ? ` to ${describePlace(shot.look_at)}` : ''}`;
        return { index, start, end: time, label, moving, party: shot.party === true };
    });
    let length = time;
    const cues: TimelineCue[] = (cinematic.cues ?? []).map((cue, index) =>
    {
        const kind = cueKind(cue);
        const seconds = cue.seconds ?? (kind === 'fade' ? 1 : 0);
        const label = kind === 'event' ? String(cue.event) : kind === 'sound' ? String(cue.sound)
            : kind === 'subtitle' ? String(cue.subtitle) : kind === 'fade' ? `fade ${cue.fade}`
            : kind === 'letterbox' ? `letterbox ${cue.letterbox ? 'in' : 'out'}` : kind === 'shake' ? `shake ${cue.shake}`
            : kind === 'monster' ? `${cue.monster} ${cue.action ?? ''}`.trim() : kind;
        length = Math.max(length, cue.at + seconds);
        return { index, start: cue.at, end: cue.at + seconds, kind, label };
    });
    return { length, shots, cues };
}

export interface CameraPose
{
    shot: number;
    party: boolean;
    position: Point3;
    target: Point3 | null;
}

export type ResolvePlace = (place: Point3 | string) => Point3 | null;

const smoothstep = (value: number) => value * value * (3 - 2 * value);

function keyPose(key: CinematicKey, resolve: ResolvePlace): { position: Point3; target: Point3 | null } | null
{
    if (key.at === undefined)
    {
        return null;
    }

    const base = resolve(key.at);

    if (!base)
    {
        return null;
    }

    const offset = key.offset ?? [0, 0, 0];
    const position: Point3 = [base[0] + offset[0], base[1] + offset[1], base[2] + offset[2]];
    let target: Point3 | null = null;

    if (key.look_at !== undefined)
    {
        target = resolve(key.look_at);
    }
    else if (key.yaw !== undefined)
    {
        // Degrees counter-clockwise from east and up: a point 1000 ahead.
        const yaw = (key.yaw * Math.PI) / 180;
        const pitch = ((key.pitch ?? 0) * Math.PI) / 180;
        target = [position[0] + 1000 * Math.cos(yaw) * Math.cos(pitch), position[1] + 1000 * Math.sin(yaw) * Math.cos(pitch),
            position[2] + 1000 * Math.sin(pitch)];
    }

    return { position, target };
}

// Where the camera is at `time` seconds from the start: the shot then, and between a moving shot's keys the eased mix
// of their places and aims. Null after the last shot, or where a place does not resolve.
export function cameraAt(cinematic: Cinematic, time: number, resolve: ResolvePlace): CameraPose | null
{
    const timeline = timelineOf(cinematic);
    const shot = timeline.shots.find((entry) => time >= entry.start && time < entry.end)
        ?? (time === timeline.shots.at(-1)?.end ? timeline.shots.at(-1) : undefined);

    if (!shot)
    {
        return null;
    }

    const source = cinematic.shots[shot.index]!;

    if (source.party)
    {
        return { shot: shot.index, party: true, position: [0, 0, 0], target: null };
    }

    const keys: CinematicKey[] = [{ ...source, seconds: 0 }, ...(source.keys ?? [])];
    const local = time - shot.start;
    let after = keys.findIndex((key) => (key.seconds ?? 0) > local);

    if (after === -1)
    {
        const last = keyPose(keys.at(-1)!, resolve);
        return last ? { shot: shot.index, party: false, ...last } : null;
    }

    after = Math.max(1, after);
    const from = keys[after - 1]!;
    const to = keys[after]!;
    const a = keyPose(from, resolve);
    const b = keyPose(to, resolve);

    if (!a || !b)
    {
        return null;
    }

    const span = (to.seconds ?? 0) - (from.seconds ?? 0);
    const raw = span > 0 ? (local - (from.seconds ?? 0)) / span : 1;
    const eased = source.easing === 'linear' ? raw : smoothstep(Math.min(1, Math.max(0, raw)));
    const mix = (p: Point3, q: Point3): Point3 => [p[0] + (q[0] - p[0]) * eased, p[1] + (q[1] - p[1]) * eased,
        p[2] + (q[2] - p[2]) * eased];
    return { shot: shot.index, party: false, position: mix(a.position, b.position),
        target: a.target && b.target ? mix(a.target, b.target) : (a.target ?? b.target) };
}
