// Walk mode's input and camera, without the browser (S5_BROWSER_EDITOR.md 3.6): the keys held as the request list's
// walk buttons, the mouse's look as the game's yaw and pitch, the party's pose as the studio's camera, and the game's
// exit pose (Play here) as a camera. The walk itself runs in the worker (walk.worker.ts).
import type { WalkPose } from '../../../schema/rpc/generated/rpc.ts';
import type { Camera } from '../model/pins.ts';
import { HALF } from '../edit/cells.ts';

// The request list's buttons (walk.rpc.json walk_buttons).
export const WALK_BUTTON = { forward: 1, back: 2, left: 4, right: 8, run: 16, jump: 32 } as const;

// The game's movement keys: WASD and the arrows, Shift runs, Space jumps (MM's defaults: arrows turn there; here the
// mouse turns, so the arrows walk and strafe like WASD).
const KEYS: Record<string, number> = {
    KeyW: WALK_BUTTON.forward, ArrowUp: WALK_BUTTON.forward,
    KeyS: WALK_BUTTON.back, ArrowDown: WALK_BUTTON.back,
    KeyA: WALK_BUTTON.left, ArrowLeft: WALK_BUTTON.left,
    KeyD: WALK_BUTTON.right, ArrowRight: WALK_BUTTON.right,
    ShiftLeft: WALK_BUTTON.run, ShiftRight: WALK_BUTTON.run,
    Space: WALK_BUTTON.jump,
};

export function isWalkKey(code: string): boolean
{
    return code in KEYS;
}

export function buttonsOf(keys: Iterable<string>): number
{
    let buttons = 0;
    for (const code of keys)
    {
        buttons |= KEYS[code] ?? 0;
    }
    return buttons;
}

// Mouse look: the yaw turns left for a move right (yaw counter-clockwise from east), pitch is clamped short of
// straight up and down as the game's camera is.
export const LOOK_RADIANS_PER_PIXEL = 0.0035;
export const PITCH_LIMIT = (89 * Math.PI) / 180;

export function look(yaw: number, pitch: number, dx: number, dy: number): { yaw: number; pitch: number }
{
    const turn = Math.PI * 2;
    const nextYaw = (((yaw - dx * LOOK_RADIANS_PER_PIXEL) % turn) + turn) % turn;
    const nextPitch = Math.max(-PITCH_LIMIT, Math.min(PITCH_LIMIT, pitch - dy * LOOK_RADIANS_PER_PIXEL));
    return { yaw: nextYaw, pitch: nextPitch };
}

// The camera at the party's eye, facing yaw and pitch.
export function cameraOfWalk(pose: WalkPose, yaw: number, pitch: number): Camera
{
    return { eye: [pose.position[0], pose.position[1], pose.eye_z], yaw, pitch };
}

// What the status bar says of the party: where, on what, in which room (indoors) or terrain cell (outdoors).
export function walkStatus(pose: WalkPose, kind: 'indoor' | 'outdoor'): string
{
    const [x, y, z] = pose.position.map((value) => Math.round(value));
    const where = kind === 'indoor'
        ? `${pose.room ?? 'no room'}${pose.sector !== undefined ? ` (sector ${pose.sector})` : ''}`
        : `cell ${Math.floor((x + HALF) / 512)},${Math.floor((HALF - y) / 512)}${pose.model !== undefined ? ` · on model ${pose.model}` : ''}${pose.on_water ? ' · water' : ''}`;
    const footing = pose.grounded ? `floor ${z}` : `in the air (${Math.round(pose.vertical_velocity ?? 0)}/s)`;
    return `walk · X ${x}  Y ${y}  Z ${z} · ${where} · ${footing}`;
}

// The game's exit pose as the studio's camera: the eye over the feet.
export function cameraOfExitPose(pose: { position: number[]; yaw_radians: number; pitch_degrees: number }, eyeHeight: number): Camera
{
    return {
        eye: [pose.position[0], pose.position[1], pose.position[2] + eyeHeight],
        yaw: pose.yaw_radians,
        pitch: (pose.pitch_degrees * Math.PI) / 180,
    };
}
