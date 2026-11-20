import { describe, expect, it } from 'vitest';
import type { Pin } from '../../../schema/rpc/generated/rpc.ts';
import { actionsFor, cameraOfPose, changeNote, EYE_HEIGHT, isClosed, needsText, pictureRoute, pinPlace, poseOfCamera, sortPins } from './pins.ts';

const pin = (id: string, status: Pin['status'], extra: Partial<Pin> = {}): Pin => ({ id, text: id, status, ...extra });

describe('pins: actions, order and places', () =>
{
    it('offers what the core allows for each status', () =>
    {
        expect(actionsFor(pin('pin:p1', 'open'))).toEqual(['claim', 'reply', 'resolve', 'decline']);
        expect(actionsFor(pin('pin:p1', undefined))).toEqual(['claim', 'reply', 'resolve', 'decline']);
        expect(actionsFor(pin('pin:p2', 'claimed', { claimed_by: 'agent:gw' }))).toEqual(['reply', 'decline']);
        expect(actionsFor(pin('pin:p2', 'claimed', { claimed_by: 'user' }))).toEqual(['reply', 'resolve', 'decline']);
        expect(actionsFor(pin('pin:p3', 'resolved'))).toEqual(['reply', 'accept', 'reopen', 'decline']);
        expect(actionsFor(pin('pin:p4', 'accepted'))).toEqual(['reply', 'reopen']);
        expect(actionsFor(pin('pin:p5', 'declined'))).toEqual(['reply', 'reopen']);
        expect(needsText('resolve')).toBe(true);
        expect(needsText('accept')).toBe(false);
        expect(isClosed(pin('pin:p4', 'accepted'))).toBe(true);
        expect(isClosed(pin('pin:p3', 'resolved'))).toBe(false);
    });

    it('lists open pins first, newest first within a status', () =>
    {
        const sorted = sortPins([pin('pin:p1', 'accepted'), pin('pin:p2', 'open'), pin('pin:p10', 'open'), pin('pin:p3', 'resolved'), pin('pin:p4', 'claimed')]);
        expect(sorted.map((p) => p.id)).toEqual(['pin:p10', 'pin:p2', 'pin:p4', 'pin:p3', 'pin:p1']);
    });

    it('places a pin at its point, else where it was made from', () =>
    {
        expect(pinPlace(pin('pin:p1', 'open', { at: [1, 2, 3], pose: { position: [9, 9, 9] } }))).toEqual([1, 2, 3]);
        expect(pinPlace(pin('pin:p1', 'open', { pose: { position: [9, 8, 7] } }))).toEqual([9, 8, 7]);
        expect(pinPlace(pin('pin:p1', 'open'))).toBeNull();
    });
});

describe('pins: the game pose and the studio camera', () =>
{
    it('puts the eye over the feet and keeps the facing (a game pin)', () =>
    {
        const camera = cameraOfPose({ position: [2816, 2048, -380], yaw_radians: 1.571, pitch_degrees: -3 }, EYE_HEIGHT.indoor);
        expect(camera.eye).toEqual([2816, 2048, -220]);
        expect(camera.yaw).toBeCloseTo(1.571, 6);
        expect(camera.pitch).toBeCloseTo((-3 * Math.PI) / 180, 9);
        // Only the heading in 2048 units: a quarter turn is north.
        expect(cameraOfPose({ position: [0, 0, 0], heading_yaw_units: 512 }, 160).yaw).toBeCloseTo(Math.PI / 2, 9);
    });

    it('turns the studio camera into the pose `loc` would print, and back', () =>
    {
        const pose = poseOfCamera({ eye: [100.12345, -50, 336], yaw: -Math.PI / 2, pitch: 0.2 }, EYE_HEIGHT.outdoor);
        expect(pose.position).toEqual([100.123, -50, 160]);
        expect(pose.yaw_radians).toBeCloseTo((3 * Math.PI) / 2, 3);
        expect(pose.heading_yaw_units).toBe(1536);
        expect(pose.pitch_degrees).toBeCloseTo(11.459, 3);
        const back = cameraOfPose(pose, EYE_HEIGHT.outdoor);
        expect(back.eye[2]).toBeCloseTo(336, 6);
        expect(back.pitch).toBeCloseTo(0.2, 4);
        expect(Math.cos(back.yaw)).toBeCloseTo(Math.cos(-Math.PI / 2), 4);
    });

    it('names the picture route and says what changed', () =>
    {
        expect(pictureRoute('devdocs/x/L4', '.oymap/pins/pictures/p7.png')).toBe('/picture/devdocs%2Fx%2FL4/.oymap%2Fpins%2Fpictures%2Fp7.png');
        expect(changeNote('agent:dress', 'lights', ['objects.yml: added light:a', 'objects.yml: added light:b'])).toBe('agent:dress: "lights" · objects.yml: added light:a (+1 more)');
        expect(changeNote('outside', '', ['rooms.yml: room:hall changed outline'])).toBe('An edit outside the studio: rooms.yml: room:hall changed outline');
    });
});
