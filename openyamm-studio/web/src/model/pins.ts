// The pins' own logic, without the UI (S5_BROWSER_EDITOR.md 3.13): which actions a pin offers, the order the panel
// lists them in, where a pin is, and the game's pose (as `loc` prints it: the party's feet, yaw in radians, pitch in
// degrees) against the studio's camera (an eye, yaw and pitch in radians). The pose is stored as the game gives it;
// only the studio converts (2.15).
import type { Pin } from '../../../schema/rpc/generated/rpc.ts';

export type PinStatus = 'open' | 'claimed' | 'resolved' | 'accepted' | 'declined';
export type PinAction = 'claim' | 'reply' | 'resolve' | 'accept' | 'reopen' | 'decline';

// The party's eye over its feet in the game (game/indoor/IndoorMovementController.h, OutdoorPartyRuntime.h).
export const EYE_HEIGHT = { indoor: 160, outdoor: 176 } as const;

export function statusOf(pin: Pin): PinStatus
{
    return (pin.status ?? 'open') as PinStatus;
}

// Open first, then claimed, resolved (waiting for the person), and the closed ones; newest first within each.
export function sortPins(pins: readonly Pin[]): Pin[]
{
    const rank: Record<PinStatus, number> = { open: 0, claimed: 1, resolved: 2, accepted: 3, declined: 4 };
    const number = (pin: Pin) => Number(/(\d+)$/.exec(pin.id)?.[1] ?? 0);
    return [...pins].sort((a, b) => rank[statusOf(a)] - rank[statusOf(b)] || number(b) - number(a));
}

export function isClosed(pin: Pin): boolean
{
    const status = statusOf(pin);
    return status === 'accepted' || status === 'declined';
}

// What `who` may do with a pin, as the core allows it (core/Pins.cpp): claim an open pin (or keep one it holds),
// resolve an open pin or its own claim, accept a resolved one, reopen a closed or resolved one, decline one not yet
// closed; a reply is always possible.
export function actionsFor(pin: Pin, who = 'user'): PinAction[]
{
    const status = statusOf(pin);
    const actions: PinAction[] = [];
    if (status === 'open' || (status === 'claimed' && pin.claimed_by === who))
    {
        actions.push('claim');
    }
    actions.push('reply');
    if (status === 'open' || (status === 'claimed' && pin.claimed_by === who))
    {
        actions.push('resolve');
    }
    if (status === 'resolved')
    {
        actions.push('accept');
    }
    if (status === 'resolved' || status === 'accepted' || status === 'declined')
    {
        actions.push('reopen');
    }
    if (status !== 'accepted' && status !== 'declined')
    {
        actions.push('decline');
    }
    return status === 'claimed' && pin.claimed_by === who ? actions.filter((action) => action !== 'claim') : actions;
}

// Whether an action needs words: what was done (resolve), why not (decline), a reply's text.
export function needsText(action: PinAction): boolean
{
    return action === 'resolve' || action === 'decline' || action === 'reply';
}

// Where a pin is on the map: its point, else where it was made from.
export function pinPlace(pin: Pin): [number, number, number] | null
{
    if (pin.at)
    {
        return pin.at;
    }
    return pin.pose?.position ?? null;
}

export interface Camera
{
    eye: [number, number, number];
    // Radians: yaw from east (+x) towards north (+y); pitch up from level.
    yaw: number;
    pitch: number;
}

export interface Pose
{
    position: [number, number, number];
    yaw_radians: number;
    pitch_degrees: number;
    heading_yaw_units: number;
}

const round = (value: number, decimals: number) => Math.round(value * 10 ** decimals) / 10 ** decimals;

// The studio's camera at a pose: the eye over the feet, facing as the party faced.
export function cameraOfPose(pose: NonNullable<Pin['pose']>, eyeHeight: number): Camera
{
    return {
        eye: [pose.position[0], pose.position[1], pose.position[2] + eyeHeight],
        yaw: pose.yaw_radians ?? (pose.heading_yaw_units !== undefined ? pose.heading_yaw_units * Math.PI / 1024 : 0),
        pitch: ((pose.pitch_degrees ?? 0) * Math.PI) / 180,
    };
}

// The pose of the studio's camera, in the game's terms (the feet under the eye; yaw in [0, 2 pi)).
export function poseOfCamera(camera: Camera, eyeHeight: number): Pose
{
    const turn = Math.PI * 2;
    const yaw = ((camera.yaw % turn) + turn) % turn;
    return {
        position: [round(camera.eye[0], 3), round(camera.eye[1], 3), round(camera.eye[2] - eyeHeight, 3)],
        yaw_radians: round(yaw, 4),
        pitch_degrees: round((camera.pitch * 180) / Math.PI, 3),
        heading_yaw_units: Math.round((yaw * 2048) / turn) % 2048,
    };
}

// The host's URL of a pin's picture (a path the pins document gives, relative to the project).
export function pictureRoute(projectKey: string, relative: string): string
{
    return `/picture/${encodeURIComponent(projectKey)}/${encodeURIComponent(relative)}`;
}

// The words of a change note: "agent:dress changed objects.yml: light:entry changed radius (900 -> 950)".
export function changeNote(author: string, label: string, changes: readonly string[]): string
{
    const who = author === 'outside' ? 'An edit outside the studio' : author;
    const what = label ? `"${label}"` : changes.length > 0 ? changes[0] : 'changed the project';
    const more = changes.length > 1 ? ` (+${changes.length - 1} more)` : '';
    return `${who}: ${what}${label && changes.length > 0 ? ` · ${changes[0]}` : ''}${more}`;
}
