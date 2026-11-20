// S5a5's models: the flow graph from a solve, the scorecard's lines from jobs and results, the compare's heat and
// the original's mesh moved to the rebuild's heights.
import { describe, expect, it } from 'vitest';
import type { CompareJobResult, Job, ViewLayoutResult, ViewOriginalMeshResult } from '../../../schema/rpc/generated/rpc.ts';
import { buildFlow, conditionText, lockNames, parseOpenedBy, placeFlow } from './flow.ts';
import type { SolveLike } from './flow.ts';
import { heatColour, latestJobs, scorecardKinds, scoreLine } from './scorecard.ts';
import { jobRoute, planHeat, regionGrid, shiftedMesh } from './compare.ts';

const layout = {
    revision: 'r', view_revision: 'r', stale: false, kind: 'indoor', world: 'mm6', bounds: { min: [0, 0, 0], max: [1, 1, 1] },
    rooms: [
        { id: 'room:hall', sector: 1, outline: [], floor: 0, ceiling: 384 },
        { id: 'room:vault', sector: 2, outline: [], floor: 0, ceiling: 384 },
        { id: 'room:cell', sector: 3, outline: [], floor: 0, ceiling: 384 },
        { id: 'room:pit', sector: 4, outline: [], floor: -512, ceiling: 0 },
    ],
    openings: [
        { id: 'open:hall_vault', from: 'room:hall', to: 'room:vault', bottom: 0, top: 256 },
        { id: 'open:vault_cell', from: 'room:vault', to: 'room:cell', bottom: 0, top: 256 },
        { id: 'open:hall_pit', from: 'room:hall', to: 'room:pit', bottom: 0, top: 256 },
    ],
    doors: [{ id: 'door:vault_gate', opening: 'open:hall_vault' }],
    lifts: [], things: [],
} as unknown as ViewLayoutResult;

const files = {
    'ids.lock.yml': { tree: { sectors: { 'room:hall': 1, 'room:vault': 2, 'room:cell': 3, 'room:pit': 4 }, events: { 'evt:lever': 7 }, doors: { 'door:vault_gate': 3 } } },
    'rooms.yml': { tree: { rooms: [{ id: 'room:hall' }, { id: 'room:vault', space: 'space:treasury' }, { id: 'room:cell' }, { id: 'room:pit' }] } },
    'plan.yml': { tree: { goals: [{ id: 'goal:loot', space: 'space:treasury' }] } },
    'objects.yml': { tree: { start: { room: 'room:hall' }, switches: [{ id: 'switch:lever', room: 'room:hall' }] } },
    'wiring.yml': { tree: { events: [
        { id: 'evt:lever', preset: 'switch', source: 'switch:lever', title: 'Lever', opens: ['door:vault_gate'], condition: { not: { map_var: 'pulled' } } },
        { id: 'evt:sign', preset: 'text', text: 'Hello' },
    ] } },
};

const solve: SolveLike = {
    sector_rooms: { 1: 'room:hall', 2: 'room:vault', 3: 'room:cell', 4: 'room:pit' },
    sectors_with_floor: 4,
    waves: [
        { sectors: [1], opened_by: [], needs: [] },
        { sectors: [2, 3], opened_by: ['event 7 (Lever) in sector 1: door 3 open'], needs: ['item 2187'] },
    ],
    never_reached: [4],
    issues: [], waiting: ['event 9 does not do this for want of map_var 2 >= 1: door 4 open'], notes: [], exits: [],
};

describe('the flow graph', () =>
{
    it('reads the wave lines and the lock', () =>
    {
        expect(parseOpenedBy('event 6 (Hoist brake) in sector 11: door 6 open')).toEqual({ event: 6, title: 'Hoist brake', door: 6, action: 'open' });
        expect(parseOpenedBy('event 1 (run by the map): door 2 toggle')).toMatchObject({ event: 1, door: 2, action: 'toggle' });
        expect(parseOpenedBy('something else')).toBeNull();
        const names = lockNames(files['ids.lock.yml'].tree);
        expect(names.doors.get(3)).toBe('door:vault_gate');
        expect(names.events.get(7)).toBe('evt:lever');
        expect(conditionText({ not: { map_var: 'pulled' } })).toBe('not map_var pulled');
        expect(conditionText({ any: [{ item: 'key' }, { qbit: 3 }] })).toBe('any (item key, qbit 3)');
    });

    it('puts rooms in the columns of their steps, names the door\'s events and marks the critical path', () =>
    {
        const graph = buildFlow(solve, layout, files);
        expect(graph.columns).toBe(2);
        const step = Object.fromEntries(graph.nodes.map((node) => [node.id, node.step]));
        expect(step).toEqual({ 'room:hall': 0, 'room:vault': 1, 'room:cell': 1, 'room:pit': null });
        expect(graph.neverReached).toEqual(['room:pit']);
        const gate = graph.edges.find((edge) => edge.id === 'open:hall_vault')!;
        expect(gate.door).toBe('door:vault_gate');
        expect(gate.openedBy).toEqual([{ event: 'evt:lever', title: 'Lever', step: 1, action: 'open' }]);
        // The start (hall) to the goal's space (the vault): through the gate.
        expect(gate.critical).toBe(true);
        expect(graph.edges.find((edge) => edge.id === 'open:hall_pit')!.critical).toBe(false);
        expect(graph.nodes.find((node) => node.id === 'room:vault')!.goal).toBe(true);
        expect(graph.nodes.find((node) => node.id === 'room:hall')!.start).toBe(true);
        const lever = graph.events.find((event) => event.id === 'evt:lever')!;
        expect(lever).toMatchObject({ source: 'switch:lever', room: 'room:hall', targets: [{ id: 'door:vault_gate', verb: 'open' }], steps: [1],
            condition: 'not map_var pulled' });
        expect(graph.needs[1]).toEqual(['item 2187']);
        expect(graph.waiting).toHaveLength(1);
        const placed = placeFlow(graph);
        expect(placed.get('room:hall')!.x).toBeLessThan(placed.get('room:vault')!.x);
        expect(placed.get('room:pit')!.x).toBeGreaterThan(placed.get('room:cell')!.x);
    });

    it('says why there is no graph outdoors, and draws rooms without a solve unplaced in steps', () =>
    {
        const outdoor = buildFlow(null, { ...layout, kind: 'outdoor', rooms: [], openings: [], doors: [] } as unknown as ViewLayoutResult, {});
        expect(outdoor.empty).toMatch(/indoor maps/);
        const unsolved = buildFlow(null, layout, files);
        expect(unsolved.nodes.every((node) => node.step === null)).toBe(true);
        expect(unsolved.columns).toBe(0);
    });
});

const job = (id: string, kind: Job['kind'], state: Job['state'], revision = 'r2', extra: Partial<Job> = {}): Job => ({
    id, kind, title: kind, project: 'p', revision, state, background: true, params: {}, created: `2026-11-15T00:00:0${id}`, started: null,
    finished: null, seconds: 1, progress: [], error: state === 'failed' ? 'it broke' : null, line: '', pictures: [], has_result: state === 'done', ...extra,
});

const compare = {
    kind: 'indoor', original: '6d01.blv', rebuilt: 'x.blv', world: 'mm6', score: 0.9812, band: { at_least: 0.97, within: true },
    parts: [{ id: 'shape', title: 'shape', weight: 0.7, score: 0.99, what: 'distances' }, { id: 'textures', title: 't', weight: 0.3, score: 0.96, what: 'textures' },
        { id: 'offsets', title: 'o', weight: 0, score: 0.5, what: 'offsets' }],
    vertical_offset: -320, worst: [{ name: 'sector 4', at: [10, 20, 30], score: 0.5, what: 'a wall missing', yaw_radians: 1 }],
    heat: { cell: 256, points: [[0, 0, 1000], [256, 0, 400], [512, 0, -1]] }, floor_missing_in_rebuild: [[512, 0, 0]], floor_only_in_rebuild: [],
    notes: [], report: {},
} as unknown as CompareJobResult;

describe('the scorecard', () =>
{
    it('lists the kinds a project needs', () =>
    {
        expect(scorecardKinds('indoor', true)).toEqual(['checks', 'compare', 'playtest']);
        expect(scorecardKinds('indoor', false)).toEqual(['checks', 'scale_bands', 'playtest']);
        expect(scorecardKinds('outdoor', true)).toEqual(['checks', 'compare', 'town_feel', 'playtest']);
    });

    it('takes the newest finished job and the one waiting for this revision', () =>
    {
        const jobs = [job('3', 'compare', 'running', 'r2'), job('2', 'compare', 'done', 'r1'), job('1', 'compare', 'done', 'r0')];
        const { done, pending } = latestJobs(jobs, 'compare', 'r2');
        expect(done!.id).toBe('2');
        expect(pending!.id).toBe('3');
        expect(latestJobs(jobs, 'compare', 'r9').pending).toBeNull();
    });

    it('reads a compare: its score against the band, its parts and worst places with a place to go to; greyed when older', () =>
    {
        const line = scoreLine('compare', job('2', 'compare', 'done', 'r1'), null, compare, 'r2');
        expect(line.figure).toBe('98.1 %');
        expect(line.verdict).toBe('good');
        expect(line.stale).toBe(true);
        expect(line.details.some((detail) => detail.text.startsWith('shape 99.0 %'))).toBe(true);
        expect(line.details.find((detail) => detail.at)?.at).toEqual([10, 20, 30]);
    });

    it('reads the checks, a failure and nothing yet', () =>
    {
        const checks = { findings: [{ code: 'click.silent', severity: 'warning', message: 'door:gate says nothing', hint: '' },
            { code: 'event.unhandled', severity: 'error', message: 'event 5 has no handler', hint: '' }],
        coplanar: { pairs: 2, as_original: 2, new: 0, original: '6d01.blv' },
        reachability: { ran: true, sectors_with_floor: 10, reached_at_start: 8, reached_doors_open: 10, unreached_sectors: [] },
        solve: { waves: [{}, {}], never_reached: [], issues: ['key behind its lock'] } };
        const line = scoreLine('checks', job('1', 'checks', 'done'), null, checks as never, 'r2');
        expect(line.figure).toBe('1 errors, 1 warnings');
        expect(line.verdict).toBe('bad');
        expect(line.details.find((detail) => detail.text.includes('door:gate'))?.id).toBe('door:gate');
        expect(line.details.some((detail) => detail.text === 'key behind its lock' && detail.verdict === 'bad')).toBe(true);
        const failed = scoreLine('scale_bands', job('4', 'scale_bands', 'failed'), null, null, 'r2');
        expect(failed).toMatchObject({ figure: 'failed', verdict: 'bad' });
        expect(scoreLine('town_feel', null, job('5', 'town_feel', 'queued'), null, 'r2').figure).toBe('waiting…');
        expect(scoreLine('playtest', null, null, null, 'r2').figure).toBe('not run');
    });

    it('colours scores as oymap compare draws them', () =>
    {
        expect(heatColour(1000)).toEqual([0, 210, 40]);
        expect(heatColour(400)).toEqual([230, 40, 40]);
        expect(heatColour(-1)).toEqual([255, 0, 255]);
    });
});

describe('compare', () =>
{
    it('moves the original to the rebuild\'s heights, copying the bytes', () =>
    {
        const positions = new Float32Array([0, 0, 10, 1, 1, 20]);
        const bytes = positions.buffer.slice(0);
        const meta = { original: '6d01.blv', world: 'mm6', kind: 'indoor', file: '.oymap/view/x.mesh', bytes: 24,
            counts: { vertices: 2, triangles: 0, faces: 0 },
            sections: { positions: { offset: 0, count: 6 }, normals: { offset: 0, count: 0 }, uvs: { offset: 0, count: 0 }, indices: { offset: 0, count: 0 },
                triangle_faces: { offset: 0, count: 0 }, face_owners: { offset: 0, count: 0 } },
            groups: [], owners: [], bounds: { min: [0, 0, 10], max: [1, 1, 20] } } as unknown as ViewOriginalMeshResult;
        const shifted = shiftedMesh(meta, bytes, -320);
        expect(Array.from(new Float32Array(shifted.bytes))).toEqual([0, 0, -310, 1, 1, -300]);
        expect(Array.from(new Float32Array(bytes))).toEqual([0, 0, 10, 1, 1, 20]);
        expect(shifted.meta.bounds.min[2]).toBe(-310);
        expect(shifted.meta.stale).toBe(false);
    });

    it('names a job\'s files on the byte route, and draws the heat', () =>
    {
        expect(jobRoute('briefs/x', { id: 'j1-ab', revision: 'r1' }, 'pictures/00 p1.png')).toBe('/job/briefs%2Fx/r1/j1-ab/pictures/00%20p1.png');
        const heat = planHeat(compare)!;
        expect(heat.cell).toBe(256);
        expect(heat.points).toHaveLength(3);
        expect(heat.worst).toEqual([{ at: [10, 20, 30], label: '1' }]);
        expect(planHeat(null)).toBeNull();
        const outdoor = { ...compare, kind: 'outdoor', heat: { cell: 8192, points: Array.from({ length: 64 }, (unused, index) => [0, 0, index]) } } as unknown as CompareJobResult;
        const grid = regionGrid(outdoor);
        expect(grid).toHaveLength(8);
        expect(grid[1][0]).toBe(8);
        expect(regionGrid(compare)).toEqual([]);
    });
});
