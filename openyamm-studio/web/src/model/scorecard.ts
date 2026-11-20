// The scorecard (S5_BROWSER_EDITOR.md 3.11): one line per check of the project, from the newest finished job of each
// kind (jobs.list; the results through jobs.status). A result belongs to the revision its job ran on and is shown
// greyed when the project has moved on; a job waiting or running for the project's revision says so.
import type {
    BuildingShotsJobResult, ChecksJobResult, CompareJobResult, Job, LightingBakeJobResult, PinsTourJobResult, PlaytestJobResult,
    ScaleBandsJobResult, TownFeelJobResult,
} from '../../../schema/rpc/generated/rpc.ts';

export type JobKind = Job['kind'];

export interface KindResults
{
    checks: ChecksJobResult;
    compare: CompareJobResult;
    scale_bands: ScaleBandsJobResult;
    town_feel: TownFeelJobResult;
    building_shots: BuildingShotsJobResult;
    pins_tour: PinsTourJobResult;
    playtest: PlaytestJobResult;
    lighting_bake: LightingBakeJobResult;
}

export type Verdict = 'good' | 'bad' | 'warn' | 'none';

export interface ScoreLine
{
    kind: JobKind;
    title: string;
    // The figure in a few words ("97.4 %", "0 errors, 3 warnings").
    figure: string;
    verdict: Verdict;
    // The job it comes from (finished), and the one waiting or running for the project's revision.
    job: Job | null;
    pending: Job | null;
    // The result is of an older revision than the project's.
    stale: boolean;
    // Lines worth a look, each with an object or a place when the check gives one.
    details: { text: string; verdict: Verdict; id?: string; at?: [number, number, number] }[];
}

export const KIND_TITLES: Record<JobKind, string> = {
    checks: 'Audit, reach and solve',
    compare: 'Compare with the original',
    scale_bands: 'Room sizes (scale bands)',
    town_feel: 'Town feel',
    building_shots: 'Buildings in the game',
    pins_tour: 'Pins in the game',
    playtest: 'Playtest',
    lighting_bake: 'Lighting bake',
};

// The kinds a scorecard lists for a project (the background ones first, then the playtest).
export function scorecardKinds(kind: string, hasOriginal: boolean): JobKind[]
{
    if (kind === 'outdoor')
    {
        return ['checks', ...(hasOriginal ? ['compare' as const] : []), 'town_feel', 'playtest'];
    }
    return ['checks', hasOriginal ? 'compare' : 'scale_bands', 'playtest'];
}

const percent = (share: number, digits = 1) => `${(share * 100).toFixed(digits)} %`;

// The newest finished job of a kind, and the one waiting or running for the revision.
export function latestJobs(jobs: readonly Job[], kind: JobKind, revision: string | null): { done: Job | null; pending: Job | null }
{
    const ofKind = jobs.filter((job) => job.kind === kind);
    const done = ofKind.find((job) => job.state === 'done' || job.state === 'failed') ?? null;
    const pending = ofKind.find((job) => (job.state === 'queued' || job.state === 'running') && (!revision || job.revision === revision)) ?? null;
    return { done, pending };
}

export function scoreLine<K extends JobKind>(kind: K, done: Job | null, pending: Job | null, result: KindResults[K] | null,
    revision: string | null): ScoreLine
{
    const line: ScoreLine = { kind, title: KIND_TITLES[kind], figure: '', verdict: 'none', job: done, pending,
        stale: Boolean(done && revision && done.revision !== revision), details: [] };
    if (!done)
    {
        line.figure = pending ? (pending.state === 'running' ? 'running…' : 'waiting…') : 'not run';
        return line;
    }
    if (done.state === 'failed')
    {
        line.figure = 'failed';
        line.verdict = 'bad';
        line.details.push({ text: done.error ?? 'failed', verdict: 'bad' });
        return line;
    }
    if (!result)
    {
        line.figure = done.line || 'done';
        return line;
    }
    switch (kind)
    {
    case 'checks': {
        const checks = result as ChecksJobResult;
        const counts = { error: 0, warning: 0, info: 0 } as Record<string, number>;
        for (const finding of checks.findings)
        {
            counts[finding.severity] = (counts[finding.severity] ?? 0) + 1;
        }
        line.figure = `${counts.error} errors, ${counts.warning} warnings`;
        line.verdict = counts.error > 0 ? 'bad' : counts.warning > 0 ? 'warn' : 'good';
        line.details.push({ text: `faces in one plane: ${checks.coplanar.pairs} pairs, ${checks.coplanar.new} new${checks.coplanar.original ? ` (against ${checks.coplanar.original})` : ''}`,
            verdict: checks.coplanar.new > 0 ? 'warn' : 'good' });
        const reach = checks.reachability;
        if (reach.ran && reach.sectors_with_floor !== undefined)
        {
            const unreached = reach.unreached_sectors?.length ?? 0;
            line.details.push({ text: `on foot from the start: ${reach.reached_at_start} of ${reach.sectors_with_floor} sectors, ${reach.reached_doors_open} with every door out of the way${unreached ? `; ${unreached} never` : ''}`,
                verdict: unreached > 0 ? 'warn' : 'good' });
        }
        if (checks.solve)
        {
            const never = checks.solve.never_reached.length;
            line.details.push({ text: `the solve: ${checks.solve.waves.length} steps; ${never} sectors never reached; ${checks.solve.issues.length} order faults`,
                verdict: checks.solve.issues.length > 0 ? 'bad' : never > 0 ? 'warn' : 'good' });
            for (const issue of checks.solve.issues)
            {
                line.details.push({ text: issue, verdict: 'bad' });
            }
        }
        for (const finding of checks.findings.filter((entry) => entry.severity !== 'info').slice(0, 40))
        {
            const id = /\b((?:room|door|evt|switch|chest|light|plate|lift|mover|thing|open):[a-z0-9_]+)/.exec(finding.message)?.[1];
            line.details.push({ text: `${finding.code}: ${finding.message}`, verdict: finding.severity === 'error' ? 'bad' : 'warn', id });
        }
        break;
    }
    case 'compare': {
        const compare = result as CompareJobResult;
        line.figure = percent(compare.score);
        line.verdict = compare.band.within ? 'good' : 'bad';
        line.details.push({ text: `band: at least ${percent(compare.band.at_least, 0)} (${compare.band.within ? 'within' : 'outside'}); against ${compare.original}`,
            verdict: line.verdict });
        for (const part of compare.parts)
        {
            line.details.push({ text: `${part.id} ${percent(part.score)}${part.weight > 0 ? ` (weight ${percent(part.weight, 0)})` : ''}: ${part.what}`,
                verdict: part.weight === 0 ? 'none' : part.score >= compare.band.at_least ? 'good' : 'warn' });
        }
        for (const worst of compare.worst.slice(0, 8))
        {
            line.details.push({ text: `${worst.name} ${percent(worst.score, 0)}: ${worst.what}`, verdict: 'warn', at: worst.at });
        }
        break;
    }
    case 'scale_bands': {
        const bands = result as ScaleBandsJobResult;
        line.figure = `${bands.below_p25} of ${bands.figures.length} below the 25th percentile`;
        line.verdict = bands.below_p25 > 0 ? 'warn' : 'good';
        for (const figure of bands.figures)
        {
            line.details.push({ text: `${figure.label}: ${figure.value} (shipped p25 ${figure.p25}, median ${figure.median}; percentile ${figure.percentile})`,
                verdict: figure.below_p25 ? 'warn' : 'good' });
        }
        break;
    }
    case 'town_feel': {
        const town = result as TownFeelJobResult;
        line.figure = `${town.outside} of ${town.rules.length} outside the shipped ranges`;
        line.verdict = town.outside > 0 ? 'warn' : 'good';
        for (const rule of [...town.rules].sort((a, b) => (a.verdict === 'out' ? 0 : 1) - (b.verdict === 'out' ? 0 : 1)))
        {
            const range = `${rule.low ?? '–'} … ${rule.high ?? '–'}`;
            line.details.push({ text: `${rule.label}: ${rule.value ?? 'n/a'} (shipped ${range})`,
                verdict: rule.verdict === 'out' ? 'warn' : rule.verdict === 'ok' ? 'good' : 'none' });
        }
        break;
    }
    case 'playtest': {
        const play = result as PlaytestJobResult;
        line.figure = `${play.passed} of ${play.runs} runs passed`;
        line.verdict = play.passed === play.runs ? 'good' : 'bad';
        for (const run of play.results)
        {
            if (!run.passed)
            {
                line.details.push({ text: run.failure ?? 'failed', verdict: 'bad' });
            }
        }
        break;
    }
    case 'building_shots': {
        const shots = result as BuildingShotsJobResult;
        line.figure = `${shots.buildings.length} buildings, ${shots.pictures} pictures`;
        line.verdict = 'none';
        break;
    }
    case 'lighting_bake': {
        // S6: the repository's Cycles bake on the build (its pictures in the Pictures tab).
        const bake = result as LightingBakeJobResult;
        const report = bake.report as Record<string, unknown>;
        line.figure = `${bake.pages.length} page(s)${typeof report.faces_lightmapped === 'number' ? `, ${report.faces_lightmapped} faces lit` : ''}`;
        line.verdict = bake.pages.length > 0 ? 'good' : 'warn';
        bake.pages.forEach((page, index) =>
        {
            line.details.push({ text: `page ${index}: ${page.width} × ${page.height}, ${page.covered} texels charted, mean light ${page.mean.toFixed(2)}`,
                verdict: page.mean > 0.05 ? 'good' : 'warn' });
        });
        if (!bake.before || !bake.after)
        {
            line.details.push({ text: 'the game took no picture before or after the bake', verdict: 'warn' });
        }
        break;
    }
    case 'pins_tour': {
        const tour = result as PinsTourJobResult;
        const taken = tour.shots.filter((shot) => shot.picture).length;
        line.figure = `${taken} of ${tour.shots.length} pins pictured`;
        line.verdict = taken === tour.shots.length ? 'good' : 'warn';
        break;
    }
    }
    return line;
}

// A score from 0 to 1 as a colour of the heat map: red at 40 % and under, yellow at 70 %, green at 100 % (as
// `oymap compare` draws its pictures); -1 (no floor in the rebuild) magenta.
export function heatColour(permille: number): [number, number, number]
{
    if (permille < 0)
    {
        return [255, 0, 255];
    }
    const value = Math.min(Math.max((permille / 1000 - 0.4) / 0.6, 0), 1);
    return [Math.round(value < 0.5 ? 230 : 230 * (1 - value) * 2), Math.round(value < 0.5 ? 40 + 380 * value : 230 - 40 * (value - 0.5)), 40];
}
