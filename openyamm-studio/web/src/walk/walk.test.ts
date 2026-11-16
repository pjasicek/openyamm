// Walk mode's input and camera (walk/input.ts) and the camera against the game's (viewport/gameCamera.ts).
import { describe, expect, it } from 'vitest';
import type { WalkPose } from '../../../schema/rpc/generated/rpc.ts';
import { WALK_BUTTON, buttonsOf, cameraOfExitPose, cameraOfWalk, isWalkKey, look, PITCH_LIMIT, walkStatus } from './input.ts';
import { gameFrameIn, studioVerticalFov } from '../viewport/gameCamera.ts';
import { cameraOfPose, poseOfCamera } from '../model/pins.ts';

const pose = (extra: Partial<WalkPose> = {}): WalkPose => ({
    position: [1843, 1664, 256], eye_z: 416, grounded: true, landed: false, bits: '', ...extra,
});

describe('walk input', () =>
{
    it('takes the game\'s keys as the request list\'s buttons', () =>
    {
        expect(buttonsOf(['KeyW'])).toBe(WALK_BUTTON.forward);
        expect(buttonsOf(['KeyW', 'ShiftLeft', 'Space'])).toBe(1 | 16 | 32);
        expect(buttonsOf(['ArrowLeft', 'KeyD'])).toBe(4 | 8);
        expect(buttonsOf(['KeyS', 'ArrowDown'])).toBe(2);
        expect(buttonsOf(['KeyQ', 'KeyE'])).toBe(0);
        expect(isWalkKey('KeyA')).toBe(true);
        expect(isWalkKey('Escape')).toBe(false);
    });

    it('turns left for a move right and keeps the pitch short of straight up and down', () =>
    {
        const turned = look(0, 0, 100, 0);
        expect(turned.yaw).toBeCloseTo(2 * Math.PI - 0.35, 6);
        expect(look(0.1, 0, -10, 0).yaw).toBeCloseTo(0.135, 6);
        expect(look(0, 1.5, 0, -10000).pitch).toBe(PITCH_LIMIT);
        expect(look(0, -1.5, 0, 10000).pitch).toBe(-PITCH_LIMIT);
    });

    it('puts the camera at the party\'s eye, and the game\'s exit pose at the eye over its feet', () =>
    {
        expect(cameraOfWalk(pose(), 0.5, -0.1)).toEqual({ eye: [1843, 1664, 416], yaw: 0.5, pitch: -0.1 });
        const camera = cameraOfExitPose({ position: [2300, 1664, 256], yaw_radians: 3.142, pitch_degrees: -5 }, 160);
        expect(camera.eye).toEqual([2300, 1664, 416]);
        expect(camera.yaw).toBe(3.142);
        expect(camera.pitch).toBeCloseTo((-5 * Math.PI) / 180, 9);
        // Play here's pose from the camera and the exit pose back: the same place.
        const back = poseOfCamera(camera, 160);
        expect(back.position).toEqual([2300, 1664, 256]);
        expect(cameraOfPose(back, 160).eye).toEqual([2300, 1664, 416]);
    });

    it('says where the party is, indoors by room and outdoors by terrain cell', () =>
    {
        expect(walkStatus(pose({ sector: 3, room: 'room:gallery' }), 'indoor'))
            .toBe('walk · X 1843  Y 1664  Z 256 · room:gallery (sector 3) · floor 256');
        expect(walkStatus(pose({ position: [-588.6, 3783.1, 487.7], grounded: false, vertical_velocity: -320, on_water: true }), 'outdoor'))
            .toBe('walk · X -589  Y 3783  Z 488 · cell 62,56 · water · in the air (-320/s)');
    });
});

describe('the camera against the game\'s', () =>
{
    it('keeps the game\'s 60 degrees in a view as wide as the game\'s or wider', () =>
    {
        expect(studioVerticalFov(16 / 9)).toBe(60);
        expect(studioVerticalFov(2.05)).toBe(60);
    });

    it('widens a narrower view until the game\'s frame fits across it', () =>
    {
        const fov = studioVerticalFov(590 / 575);
        const horizontal = (aspect: number, vertical: number) => 2 * Math.atan(Math.tan((vertical * Math.PI) / 360) * aspect);
        // The view's horizontal field of view is the game's at 16:9.
        expect(horizontal(590 / 575, fov)).toBeCloseTo(horizontal(16 / 9, 60), 9);
        expect(fov).toBeCloseTo(90.02, 2);
    });

    it('places the game\'s frame inside the view', () =>
    {
        expect(gameFrameIn(1600, 900)).toEqual({ left: 0, top: 0, width: 1600, height: 900 });
        const wide = gameFrameIn(1600, 600);
        expect(wide.left).toBeCloseTo(266.667, 3);
        expect(wide.width).toBeCloseTo(1066.667, 3);
        expect([wide.top, wide.height]).toEqual([0, 600]);
        const narrow = gameFrameIn(640, 720);
        expect(narrow.width).toBe(640);
        expect(narrow.height).toBeCloseTo(360, 9);
        expect(narrow.top).toBeCloseTo(180, 9);
    });
});
