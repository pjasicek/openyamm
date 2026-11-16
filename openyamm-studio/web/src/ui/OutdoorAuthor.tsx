// Author mode outdoors (S5b2; S5_BROWSER_EDITOR.md 3.9, 3.18, W2): the outdoor tools' options above the views, the
// rail's extras (the town-feel figures where the author works, "+ event" in Wire), and the project settings' mark
// that the land is made by hand. The tools themselves are edit/outdoortools.ts.
import { useMemo, useState } from 'react';
import { Toggle } from '@base-ui/react/toggle';
import type { TownFeelJobResult } from '../../../schema/rpc/generated/rpc.ts';
import type { OutdoorOptions, ToolName } from '../edit/stages.ts';
import { DEFAULT_OUTDOOR, STRUCTURE_KINDS } from '../edit/stages.ts';
import { planBuildings, populations } from '../edit/outdoortools.ts';
import { NumberInput, TextInput } from '../form/inputs.tsx';
import { latestJobs, scoreLine } from '../model/scorecard.ts';
import { NONE } from '../state/store.ts';
import { useActions, useS, useStudioContext } from './context.ts';
import css from './Author.module.css';
import own from './OutdoorAuthor.module.css';

function Option({ label, children, title }: { label: string; children: React.ReactNode; title?: string })
{
    return <label className={css.option} title={title}><span className={css.optionLabel}>{label}</span>{children}</label>;
}

// The tools' settings outdoors (3.9: the active tool's settings, never the selection's).
export function OutdoorOptionsBar({ tool }: { tool: ToolName })
{
    const { store } = useStudioContext();
    const actions = useActions();
    const o = useS((s) => s.toolOptions.outdoor ?? DEFAULT_OUTDOOR);
    const files = useS((s) => (s.project.state === 'ready' ? s.project.value.files : undefined));
    const set = (change: Partial<OutdoorOptions>) => store.setState((s) => ({ toolOptions: { ...s.toolOptions, outdoor: { ...(s.toolOptions.outdoor ?? DEFAULT_OUTDOOR), ...change } } }));
    const number = (name: keyof OutdoorOptions, label: string, extra: { min?: number; max?: number; title?: string } = {}) => (
        <Option label={label} title={extra.title}><NumberInput value={o[name] as number} onCommit={(value) => set({ [name]: value })} width="narrow" testId={`option-${name}`} {...extra} /></Option>
    );
    const text = (name: keyof OutdoorOptions, label: string, placeholder: string) => (
        <Option label={label}><TextInput value={o[name] as string} onCommit={(value) => set({ [name]: value })} placeholder={placeholder} testId={`option-${name}`} /></Option>
    );
    const pick = (name: keyof OutdoorOptions, values: readonly string[], label: string, labels?: Record<string, string>) => (
        <Option label={label}>
            <select className={css.select} value={String(o[name])} data-testid={`option-${name}`}
                onChange={(event) => set({ [name]: typeof o[name] === 'number' ? Number(event.target.value) : event.target.value })}>
                {values.map((value) => <option key={value} value={value}>{labels?.[value] ?? value}</option>)}
            </select>
        </Option>
    );
    const toggle = (name: keyof OutdoorOptions, label: string, title: string) => (
        <Toggle className={css.toggle} pressed={Boolean(o[name])} onPressedChange={(on) => set({ [name]: on })} title={title} data-testid={`option-${name}`}>{label}</Toggle>
    );
    const half = toggle('halfCells', 'half cells', 'Points on half cells (else whole cells; Shift while clicking gives half cells too)');
    const spaces = useMemo(() =>
    {
        const list = files?.['plan.yml']?.tree.spaces;
        return Array.isArray(list) ? list.map((space) => String((space as Record<string, unknown>).id ?? '')).filter(Boolean) : [];
    }, [files]);
    switch (tool)
    {
    case 'select':
        return number('heightStep', 'PgUp/PgDn step', { min: 1, title: 'A height under the cursor (a height point, a terrace, a ridge, a road\'s bed) changes by this much' });
    case 'spots':
        return number('spotHeight', 'paint height', { min: 0, max: 8160, title: 'What a click or a drag over the spots sets (map units; Alt click a spot takes its height)' });
    case 'sculpt':
        return (
            <>
                {pick('brushMode', ['raise', 'lower', 'smooth', 'flatten'], 'mode')}
                {number('brushRadius', 'radius (cells)', { min: 1, max: 16 })}
                {o.brushMode === 'raise' || o.brushMode === 'lower' ? number('brushStrength', 'strength', { min: 8, max: 512, title: 'Map units at the brush\'s middle each dab (dabs every third of the radius)' }) : null}
            </>
        );
    case 'patch':
        return <span className={css.optionLabel}>at most 32 × 32 cells, 16 patches</span>;
    case 'hpoint':
    case 'spire':
    case 'cut':
        return number('height', tool === 'cut' ? 'floor' : 'height', { min: 0, max: 8160 });
    case 'ridge':
        return <>{number('height', 'height', { min: 0, max: 8160 })}{number('ridgeWidth', 'width (nodes)', { min: 1, max: 8 })}{number('ridgeSlope', 'slope (cells)', { min: 0, max: 16 })}{half}</>;
    case 'cliff':
        return <>{number('cliffDrop', 'drop', { min: 0 })}{pick('cliffDown', ['right', 'left'], 'low side')}{half}</>;
    case 'terrace':
        return <>{number('height', 'height', { min: 0, max: 8160 })}{number('terraceSlope', 'slope (cells)', { min: 0, max: 16 })}{half}</>;
    case 'rough':
        return number('roughAmount', 'amount', { min: 1, max: 256 });
    case 'peaks':
        return <>{number('peaksCount', 'count', { min: 1, max: 2000 })}{number('peaksLow', 'from', { min: 0, max: 8160 })}{number('peaksHigh', 'to', { min: 0, max: 8160 })}</>;
    case 'rim':
        return <>{pick('rimForm', ['level', 'ridge'], 'form')}{o.rimForm === 'level' ? number('height', 'height', { min: 0, max: 8160 }) : <>{number('peaksLow', 'tops from')}{number('peaksHigh', 'to')}</>}</>;
    case 'water':
        return <>{pick('waterKind', ['pond', 'lake', 'inlet', 'sea'], 'kind')}{number('waterLevel', 'level', { min: 0, title: '0: a step under the lowest land on the outline' })}{text('tileSet', 'tile set', 'the world\'s water')}</>;
    case 'river':
        return <>{number('riverWidth', 'width (cells)', { min: 1, max: 8 })}{number('waterLevel', 'level', { min: 0, title: '0: a step under the lowest land on its line' })}</>;
    case 'road':
        return <>{pick('roadWidth', ['lane', 'road', 'high_road'], 'width')}{text('roadSurface', 'surface', 'pebbles, cobbles, dirt')}{toggle('roadSteps', 'square / 45°', 'Each point steps square or at 45 degrees from the last (the road tiles\' directions); Alt while clicking: any angle')}</>;
    case 'district':
        return <>{pick('districtSpace', ['', ...spaces], 'for space', { '': '(a new district)' })}{o.districtSpace ? null : text('districtName', 'name', 'Market quarter')}{half}</>;
    case 'plot':
        return <PlotOptions set={set} />;
    case 'building':
        return (
            <>
                {pick('roof', ['hip', 'gable', 'flat', 'lean_to', 'cone', 'dome', 'none'], 'roof')}
                {number('roofPitch', 'pitch°', { min: 0, max: 80, title: '0: the world\'s own (mm6 128 high)' })}
                {pick('facing', ['s', 'e', 'n', 'w'], 'front')}
                {text('kit', 'kit', 'the world\'s ordinary')}
            </>
        );
    case 'structure':
        return <>{pick('structureKind', STRUCTURE_KINDS, 'kind')}{o.structureKind === 'decoration' ? text('decoration', 'decoration', 'tree12 (or the Library)') : null}{half}</>;
    case 'ground':
        return <>{text('groundMaterial', 'kind of land', 'sand, snow, swamp')}{number('groundRadius', 'radius (cells)', { min: 1, max: 16 })}</>;
    case 'scatter':
        return (
            <>
                {text('decoration', 'decoration', 'tree12 (or the Library)')}
                {number('scatterCount', 'count', { min: 1 })}
                {o.scatterLine ? null : number('scatterSpacing', 'spacing (cells)', { min: 0 })}
                {toggle('scatterLine', 'a row', 'A row along a line (a hedge, an avenue) instead of an area')}
            </>
        );
    case 'area':
    {
        const known = populations(files);
        return (
            <>
                {pick('areaKind', ['encounter', 'items', 'keep_clear', 'open'], 'kind')}
                {toggle('areaCircle', 'circle', 'Drag a circle from its middle instead of clicking an outline')}
                {o.areaKind === 'encounter' ? pick('areaSlot', ['1', '2', '3'], 'slot') : null}
                {o.areaKind === 'encounter' || o.areaKind === 'items' ? number('areaCount', 'markers', { min: 1 }) : null}
                {o.areaKind === 'encounter' ? (
                    <Option label="population" title="A plan population of the map's monsters; a new name makes one in the space the area lies in">
                        <input className={own.combo} list="outdoor-populations" defaultValue={o.areaPopulation} key={o.areaPopulation} data-testid="option-areaPopulation"
                            onBlur={(event) => set({ areaPopulation: event.target.value.trim() })}
                            onKeyDown={(event) => event.key === 'Enter' && (event.target as HTMLInputElement).blur()} />
                        <datalist id="outdoor-populations">{known.map((id) => <option key={id} value={id} />)}</datalist>
                    </Option>
                ) : null}
            </>
        );
    }
    case 'actor':
        return (
            <>
                {text('monster', 'monster', 'Peasant (or the Library)')}
                {number('actorCount', 'count', { min: 1, max: 64 })}
                {toggle('actorHostile', 'hostile', 'Hostile from the start, whatever the monster table says')}
                <button type="button" className={css.button} onClick={() => store.setState({ drawerTab: 'library' })} title="The Library's monsters: drag one onto the plan">Library…</button>
            </>
        );
    case 'arrival':
        return <>{pick('pointKind', ['entrance', 'landmark'], 'kind')}{o.pointKind === 'entrance' ? pick('pointFacing', ['n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw'], 'facing') : null}</>;
    default:
        void actions;
        return null;
    }
}

// A plot's plan building (the district's space's buildings; one added here) and its front.
function PlotOptions({ set }: { set: (change: Partial<OutdoorOptions>) => void })
{
    const actions = useActions();
    const o = useS((s) => s.toolOptions.outdoor ?? DEFAULT_OUTDOOR);
    const files = useS((s) => (s.project.state === 'ready' ? s.project.value.files : undefined));
    const buildings = planBuildings(files);
    const [name, setName] = useState('');
    const spaces = useMemo(() =>
    {
        const districts = files?.['sketch.yml']?.tree.districts;
        return Array.isArray(districts) ? districts.map((district) => String((district as Record<string, unknown>).space ?? '')).filter(Boolean) : [];
    }, [files]);
    return (
        <>
            <Option label="building">
                <select className={css.select} value={o.plotBuilding} data-testid="option-plotBuilding" onChange={(event) => set({ plotBuilding: event.target.value })}>
                    <option value="">(the district's first)</option>
                    {buildings.map((entry) => <option key={entry.id} value={entry.id}>{entry.id} {entry.footprint.join('×')}</option>)}
                </select>
            </Option>
            <Option label="front">
                <select className={css.select} value={o.plotFacing} data-testid="option-plotFacing" onChange={(event) => set({ plotFacing: event.target.value as OutdoorOptions['plotFacing'] })}>
                    {['s', 'e', 'n', 'w'].map((side) => <option key={side} value={side}>{side}</option>)}
                </select>
            </Option>
            <Option label="new plan building"><TextInput value={name} onCommit={setName} placeholder="house_baker" testId="option-new-building" /></Option>
            <button type="button" className={css.button} disabled={!name.trim() || spaces.length === 0} data-testid="add-plan-building"
                title="A house of 2 × 2 cells in the plan of the first district's space (its footprint and services in the inspector of plan.yml)"
                onClick={() =>
                {
                    const space = spaces[0];
                    const spaceList = files?.['plan.yml']?.tree.spaces;
                    const entry = Array.isArray(spaceList) ? spaceList.find((item) => (item as Record<string, unknown>).id === space) as Record<string, unknown> | undefined : undefined;
                    const id = `building:${name.trim().replace(/^building:/, '').replace(/[^a-z0-9_]/g, '_')}`;
                    const value = { id, type: 'house', count: 1, footprint_cells: [2, 2] };
                    void actions.edit({ label: `plan building ${id}`, ops: [{ op: 'patch', id: space, file: 'plan.yml',
                        patch: [Array.isArray(entry?.buildings) ? { op: 'add', path: '/buildings/-', value } : { op: 'add', path: '/buildings', value: [value] }] }] })
                        .then((result) => { if (result) { set({ plotBuilding: id }); setName(''); } });
                }}>+ plan building</button>
        </>
    );
}

// Below the outdoor tools: the town-feel figures of the newest town_feel job where the author works (W2 step 4), and in
// the Wire stage "+ event" (an event nobody clicks: on entering, by the clock).
export function OutdoorRailExtras()
{
    const actions = useActions();
    const stage = useS((s) => s.stage);
    const revision = useS((s) => (s.project.state === 'ready' ? s.project.value.revision : null));
    const jobs = useS((s) => (s.jobs.state === 'ready' ? s.jobs.value : NONE));
    const results = useS((s) => s.jobResults);
    const python = useS((s) => s.python);
    const { done, pending } = latestJobs(jobs, 'town_feel', revision);
    const line = scoreLine('town_feel', done, pending, done ? (results[done.id] as TownFeelJobResult | undefined) ?? null : null, revision);
    return (
        <>
            {stage === 4 ? (
                <div className={own.extra}>
                    <button type="button" className={css.button} data-testid="add-event"
                        title="An event of the map nobody clicks: on entering the map (load), by the clock (timer, daily, weekly); its conditions and steps in the event form"
                        onClick={() => void actions.edit({ label: 'new event', ops: [{ op: 'add', to: 'events', file: 'sketch.yml', value: { trigger: 'load' } }] }).then((result) =>
                        {
                            const made = result?.ids_allocated?.find((entry) => entry.startsWith('sketch.yml#'));
                            if (made)
                            {
                                actions.select({ id: made.slice(made.indexOf('#') + 1), file: 'sketch.yml' });
                            }
                        })}>+ event</button>
                    <p className={css.later}>What a building's door or a structure's click does: select it; the inspector's Click section (house, conditions, steps).</p>
                </div>
            ) : null}
            <section className={own.townFeel} data-testid="town-feel">
                <h4 className={own.townTitle}>Town feel <span className={line.verdict === 'warn' ? own.warn : line.verdict === 'good' ? own.good : own.dim}>{line.figure}</span></h4>
                {line.stale ? <p className={own.dim}>of an earlier revision</p> : null}
                <ul className={own.rules}>
                    {line.details.slice(0, 8).map((detail, index) => (
                        <li key={index} className={detail.verdict === 'warn' ? own.warn : detail.verdict === 'good' ? undefined : own.dim}>{detail.text}</li>
                    ))}
                </ul>
                {python ? (
                    <button type="button" className={css.button} disabled={Boolean(pending)} data-testid="run-town-feel" onClick={() => actions.startJob('town_feel')}
                        title="town_feel.py over the built map (a job): relief, flat share, houses' setbacks and lanes, services' ranks">{pending ? 'running…' : 'Run town feel'}</button>
                ) : <p className={own.dim}>This host does not run the Python checks.</p>}
            </section>
        </>
    );
}

// The project settings' mark (D15 extended): this map's land is made by hand, so the brush may sculpt anywhere; a
// person's only, refused on a rebuild.
export function HandMadeSetting()
{
    const actions = useActions();
    const files = useS((s) => (s.project.state === 'ready' ? s.project.value.files : undefined));
    const heights = files?.['sketch.yml']?.tree.heights as Record<string, unknown> | undefined;
    const marked = heights?.hand_made === true;
    const stats = files?.['project.yml']?.tree.map_stats as Record<string, unknown> | undefined;
    const rebuild = typeof stats?.reference === 'string' && stats.reference.length > 0;
    return (
        <section className={css.settingsSection}>
            <h4>Land</h4>
            {rebuild ? <p className={css.dim}>A rebuild of {String(stats!.reference)}: its land is described (the brush works inside sculpt patches only).</p> : (
                <>
                    <p>{marked ? 'This map\'s land is made by hand: the brush sculpts and smooths anywhere; agents read the land through terrain queries.'
                        : 'The land is described by its words: the brush works inside sculpt patches (at most 32 × 32 cells) only.'}</p>
                    <label className={own.check}>
                        <input type="checkbox" checked={marked} data-testid="hand-made"
                            onChange={(event) => void actions.edit({ label: event.target.checked ? 'land made by hand' : 'land described again', ops: [{ op: 'set_value', file: 'sketch.yml', path: 'heights.hand_made', value: event.target.checked ? true : null }] })} />
                        This map's land is made by hand
                    </label>
                </>
            )}
        </section>
    );
}
