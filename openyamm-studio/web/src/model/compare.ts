// Compare with the original (S5_BROWSER_EDITOR.md 3.14; S5a5): the original's mesh made ready for the 3D view beside
// the rebuild, a job's byte route, and the plan's heat from compare.run's answer.
import type { CompareJobResult, Job, ViewMeshResult, ViewOriginalMeshResult } from '../../../schema/rpc/generated/rpc.ts';

// view.original_mesh's answer as the 3D view takes a mesh, its positions moved up by `verticalOffset` (compare.run's
// vertical_offset: how much higher the whole rebuild lies), so the two views line up at one camera. The bytes are
// copied; the core's file is never changed.
export function shiftedMesh(meta: ViewOriginalMeshResult, bytes: ArrayBuffer, verticalOffset: number): { meta: ViewMeshResult; bytes: ArrayBuffer }
{
    const copy = bytes.slice(0);
    if (verticalOffset !== 0)
    {
        const positions = new Float32Array(copy, meta.sections.positions.offset, meta.sections.positions.count);
        for (let index = 2; index < positions.length; index += 3)
        {
            positions[index] += verticalOffset;
        }
    }
    const bounds = {
        min: [meta.bounds.min[0], meta.bounds.min[1], meta.bounds.min[2] + verticalOffset],
        max: [meta.bounds.max[0], meta.bounds.max[1], meta.bounds.max[2] + verticalOffset],
    } as ViewMeshResult['bounds'];
    const revision = '0'.repeat(32);
    return {
        meta: { revision, view_revision: revision, stale: false, lock_hash: 'none', kind: meta.kind, world: meta.world, file: meta.file,
            bytes: meta.bytes, counts: meta.counts, sections: meta.sections, groups: meta.groups, owners: meta.owners, bounds },
        bytes: copy,
    };
}

// A job's file on the host's byte route (pictures and its log).
export function jobRoute(key: string, job: Pick<Job, 'id' | 'revision'>, relative: string): string
{
    return `/job/${encodeURIComponent(key)}/${job.revision}/${job.id}/${relative.split('/').map(encodeURIComponent).join('/')}`;
}

// What the plan draws of a compare: every stand point's (or block's) square coloured by its score, the floor only
// one map has, and the worst places numbered.
export interface PlanHeat
{
    cell: number;
    points: readonly (readonly number[])[];
    missing: readonly (readonly number[])[];
    extra: readonly (readonly number[])[];
    worst: { at: readonly number[]; label: string }[];
}

export function planHeat(result: CompareJobResult | null): PlanHeat | null
{
    if (!result)
    {
        return null;
    }
    return {
        cell: result.heat.cell,
        points: result.heat.points,
        missing: result.floor_missing_in_rebuild,
        extra: result.floor_only_in_rebuild,
        worst: result.worst.map((place, index) => ({ at: place.at, label: String(index + 1) })),
    };
}

// The regions of an outdoor compare as rows of the 8 x 8 grid (A1 the north-west), from its heat points.
export function regionGrid(result: CompareJobResult): number[][]
{
    if (result.kind !== 'outdoor')
    {
        return [];
    }
    const rows: number[][] = [];
    result.heat.points.forEach((point, index) =>
    {
        const row = Math.floor(index / 8);
        (rows[row] ??= []).push(point[2]);
    });
    return rows;
}
