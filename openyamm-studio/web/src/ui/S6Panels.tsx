// The drawer's Cinematics and Overlay panels (devdocs/map_studio/S6_PLAN.md items C and O).
// Cinematics: wiring.yml `cinematics` as a timeline (shots back to back, cues at their seconds) with a scrubber that
// says where the camera is then, as the game moves it (model/cinematics.ts). Overlay: an overlay project's scene
// things on its base map (view.overlay): what the project adds, changes and removes, on a small plan; in Author mode
// with tools of its own (model/overlayEdit.ts).
import { useEffect, useMemo, useState } from 'react';
import type { FileTrees, JsonValue, ViewOverlayResult } from '../../../schema/rpc/generated/rpc.ts';
import { cameraAt, readCinematics, timelineOf } from '../model/cinematics.ts';
import type { Cinematic, Point3 } from '../model/cinematics.ts';
import { KIND_NAMES, overlayFrame, summariseOverlay } from '../model/overlay.ts';
import type { OverlayThing } from '../model/overlay.ts';
import { ADDED_FIELDS, CHANGE_FIELDS, LIST_OF_KIND, addedOf, changeOf, fieldText, heightNear, ladderMove, overlayOps, parseField, suggestedId } from '../model/overlayEdit.ts';
import type { NewList, OverlayGesture } from '../model/overlayEdit.ts';
import { useActions, useS } from './context.ts';
import css from './S6.module.css';

const WIDTH = 720;
const ROW = 22;

function Timeline({ cinematic, time }: { cinematic: Cinematic; time: number })
{
    const timeline = useMemo(() => timelineOf(cinematic), [cinematic]);
    const length = Math.max(timeline.length, 0.001);
    const x = (seconds: number) => 8 + (seconds / length) * (WIDTH - 16);
    const cueRows = Math.max(1, timeline.cues.length);
    const height = 26 + ROW + 6 + cueRows * 16 + 8;
    const ticks = [];

    for (let second = 0; second <= Math.floor(length); second += length > 30 ? 5 : 1)
    {
        ticks.push(
            <g key={second}>
                <line className={css.ruler} x1={x(second)} x2={x(second)} y1={14} y2={20} />
                <text className={css.tick} x={x(second) + 2} y={11}>{second}s</text>
            </g>);
    }

    return (
        <svg className={css.timeline} viewBox={`0 0 ${WIDTH} ${height}`} role="img" aria-label="The cinematic's timeline">
            <line className={css.ruler} x1={8} x2={WIDTH - 8} y1={20} y2={20} />
            {ticks}
            {timeline.shots.map((shot) => (
                <g key={shot.index}>
                    <rect className={shot.party ? css.shotParty : css.shot} x={x(shot.start)} y={26}
                        width={Math.max(2, x(shot.end) - x(shot.start) - 2)} height={ROW} rx={3} />
                    <text className={css.shotLabel} x={x(shot.start) + 5} y={26 + 15}>
                        {`${shot.index + 1}${shot.moving ? ' (moving)' : ''}: ${shot.label}`.slice(0, Math.max(4, Math.floor((x(shot.end) - x(shot.start)) / 6.2)))}
                    </text>
                </g>))}
            {timeline.cues.map((cue, row) => (
                <g key={cue.index}>
                    {cue.end > cue.start ? <rect className={css.cueSpan} x={x(cue.start)} y={26 + ROW + 6 + row * 16}
                        width={Math.max(2, x(cue.end) - x(cue.start))} height={12} rx={2} /> : null}
                    <circle className={cue.kind === 'event' ? css.cueEvent : css.cue} cx={x(cue.start)} cy={26 + ROW + 12 + row * 16} r={4} />
                    <text className={css.cueLabel} x={x(cue.start) + 8} y={26 + ROW + 16 + row * 16}>{`${cue.kind}: ${cue.label}`}</text>
                </g>))}
            <line className={css.playhead} x1={x(time)} x2={x(time)} y1={14} y2={height - 4} />
        </svg>
    );
}

export function CinematicsPanel()
{
    const actions = useActions();
    const tree = useS((s) => (s.project.state === 'ready' ? s.project.value.files['wiring.yml']?.tree : undefined));
    const layout = useS((s) => (s.layout.state === 'ready' ? s.layout.value : null));
    const base = useS((s) => (s.project.state === 'ready' ? (s.project.value.files['project.yml']?.tree as Record<string, unknown> | undefined)?.base : undefined));
    const revision = useS((s) => (s.project.state === 'ready' ? s.project.value.revision : ''));
    const cinematics = useMemo(() => readCinematics(tree), [tree]);
    // An overlay project (S8a): its things' places come from view.overlay, and a cinematic of a base one's name
    // replaces it.
    const [overlay, setOverlay] = useState<ViewOverlayResult | null>(null);
    useEffect(() =>
    {
        let live = true;
        if (typeof base === 'string')
        {
            actions.sceneOverlay().then((value) => { if (live) setOverlay(typeof value === 'string' ? null : value); });
        }
        return () => { live = false; };
    }, [actions, base, revision]);
    const [chosen, setChosen] = useState(0);
    const [time, setTime] = useState(0);
    const cinematic = cinematics[Math.min(chosen, cinematics.length - 1)];
    const timeline = useMemo(() => (cinematic ? timelineOf(cinematic) : null), [cinematic]);

    if (!cinematic || !timeline)
    {
        return (
            <div className={css.panel} data-testid="cinematics-panel">
                <p className={css.summary}>No cinematics. They are wiring.yml `cinematics`: camera shots with cues on a timeline, played by the effect {'{cinematic: <id>}'}.</p>
            </div>);
    }

    // An object's id: the layout's thing or room of that id.
    const resolve = (place: Point3 | string): Point3 | null =>
    {
        if (typeof place !== 'string')
        {
            return place;
        }

        const thing = layout?.things?.find((entry) => entry.id === place) ?? overlay?.things.find((entry) => entry.id === place);

        if (thing)
        {
            return [thing.at[0], thing.at[1], thing.at[2]];
        }

        const room = layout?.rooms?.find((entry) => entry.id === place);

        if (room?.outline)
        {
            const sum = room.outline.reduce((acc, [px, py]) => [acc[0] + px, acc[1] + py], [0, 0]);
            return [sum[0] / room.outline.length, sum[1] / room.outline.length, room.floor + 160];
        }

        return null;
    };
    const pose = cameraAt(cinematic, Math.min(time, timeline.length), resolve);
    const round = (point: Point3) => `[${point.map((value) => Math.round(value)).join(', ')}]`;

    return (
        <div className={css.panel} data-testid="cinematics-panel">
            <div className={css.row}>
                {cinematics.map((entry, index) => (
                    <button key={entry.id} type="button" className={index === chosen ? css.pickOn : css.pick}
                        onClick={() => { setChosen(index); setTime(0); }}>{entry.id}</button>))}
                <span className={css.dim}>{`${timeline.length.toFixed(1)} s, ${timeline.shots.length} shots, ${timeline.cues.length} cues${cinematic.skippable === false ? ', not skippable' : ''}`}
                    {overlay?.cinematics?.some((entry) => entry.id === cinematic.id && entry.state === 'replaced') ? `; replaces the base map's ${cinematic.id}` : ''}</span>
            </div>
            <Timeline cinematic={cinematic} time={Math.min(time, timeline.length)} />
            <input className={css.scrub} type="range" min={0} max={timeline.length} step={0.05} value={Math.min(time, timeline.length)}
                aria-label="Time in the cinematic" onChange={(event) => setTime(Number(event.target.value))} />
            <div className={css.camera} data-testid="cinematic-camera">
                {`${Math.min(time, timeline.length).toFixed(2)} s: `}
                {pose === null ? 'after the last shot, or a place that names nothing'
                    : pose.party ? `shot ${pose.shot + 1}, the party's own view`
                    : `shot ${pose.shot + 1}, camera ${round(pose.position)}${pose.target ? ` looking at ${round(pose.target)}` : ''}`}
            </div>
        </div>
    );
}

// The Overlay tab's tools (S6, the second run; S8a): in Author mode the things on the plan are picked and changed,
// taken out and put back, and new lights, sounds, spawn points, ladders, monsters and floor items are placed by a click
// (model/overlayEdit.ts says what each gesture writes; one patch of objects.yml `scene` each, through the edit
// session). The project's own things move; so does a base ladder (by its `offset`).
type PlaceTool = 'light' | 'sound' | 'spawn' | 'ladder' | 'monster' | 'item';
type OverlayTool = 'select' | PlaceTool | 'move';
const TOOLS: readonly OverlayTool[] = ['select', 'light', 'sound', 'spawn', 'ladder', 'monster', 'item', 'move'];
const TOOL_LIST: Record<PlaceTool, NewList> = {
    light: 'lights', sound: 'sounds', spawn: 'spawns', ladder: 'ladders', monster: 'monsters', item: 'items',
};
const TOOL_WORDS: Record<OverlayTool, string> = {
    select: 'Pick', light: 'Add a light', sound: 'Add a sound', spawn: 'Add a spawn point', ladder: 'Add a ladder',
    monster: 'Add a monster', item: 'Add an item', move: 'Move the picked one',
};
const movable = (thing: OverlayThing | null) => thing !== null && (thing.origin === 'added' || (thing.kind === 'ladder' && thing.state !== 'removed'));

function ThingForm({ thing, files, onEdit }: { thing: OverlayThing; files: FileTrees | undefined; onEdit: (gesture: OverlayGesture, label: string) => void })
{
    const added = thing.origin === 'added';
    const list = LIST_OF_KIND[thing.kind];
    const current: Record<string, JsonValue | undefined> = added ? (addedOf(files, list, thing.id) ?? {}) : (changeOf(files, thing.id)?.entry ?? {});
    const fields = added ? ADDED_FIELDS[list] ?? [] : CHANGE_FIELDS[thing.kind];
    const [texts, setTexts] = useState<Record<string, string>>({});
    const [problem, setProblem] = useState<string | null>(null);
    const key = `${thing.id}:${JSON.stringify(current)}`;
    useEffect(() => { setTexts({}); setProblem(null); }, [key]);
    const textOf = (name: string) => texts[name] ?? fieldText(current[name]);
    const apply = () =>
    {
        const changed: Record<string, JsonValue | null> = {};
        for (const field of fields)
        {
            if (texts[field.name] === undefined)
            {
                continue;
            }
            const value = parseField(field.type, texts[field.name]!);
            if (value === undefined)
            {
                setProblem(`${field.label}: not of its form`);
                return;
            }
            changed[field.name] = value;
        }
        if (Object.keys(changed).length === 0)
        {
            return;
        }
        onEdit(added ? { kind: 'set', list, id: thing.id, fields: changed } : { kind: 'change', of: thing.id, fields: changed },
            `${added ? 'change' : 'change the base map\'s'} ${thing.id}`);
    };
    return (
        <div className={css.form} data-testid="overlay-form">
            <div className={css.heading}>{`${thing.id} · ${KIND_NAMES[thing.kind]} · ${thing.state}`}</div>
            <div className={css.dim}>{added ? `The project's own, at [${thing.at.join(', ')}].` : `The base map's, at [${thing.at.join(', ')}]: a change names only the words that differ (objects.yml scene.changes).`}</div>
            {thing.state === 'removed' ? null : fields.map((field) => (
                <label key={field.name} className={css.field}>
                    <span>{field.label}</span>
                    <input className={css.input} value={textOf(field.name)} placeholder={added ? 'default' : 'as the base map has it'}
                        data-testid={`overlay-field-${field.name}`} onChange={(event) => setTexts({ ...texts, [field.name]: event.target.value })}
                        onKeyDown={(event) => { if (event.key === 'Enter') apply(); }} />
                </label>))}
            {problem ? <div className={css.bad}>{problem}</div> : null}
            <div className={css.row}>
                {thing.state !== 'removed' && fields.length > 0
                    ? <button type="button" className={css.pickOn} data-testid="overlay-apply" onClick={apply}>Apply</button> : null}
                {added ? <button type="button" className={css.pick} data-testid="overlay-delete"
                    onClick={() => onEdit({ kind: 'delete', list, id: thing.id }, `delete ${thing.id}`)}>Delete</button> : null}
                {!added && thing.state !== 'removed' ? <button type="button" className={css.pick} data-testid="overlay-remove"
                    onClick={() => onEdit({ kind: 'remove', of: thing.id }, `take out ${thing.id}`)}>Take it out</button> : null}
                {thing.state === 'removed' ? <button type="button" className={css.pick} data-testid="overlay-restore"
                    onClick={() => onEdit({ kind: 'restore', of: thing.id }, `put back ${thing.id}`)}>Put it back</button> : null}
            </div>
        </div>
    );
}

export function OverlayPanel()
{
    const actions = useActions();
    const card = useS((s) => (s.project.state === 'ready' ? s.project.value.files['project.yml']?.tree as Record<string, unknown> | undefined : undefined));
    const files = useS((s) => (s.project.state === 'ready' ? s.project.value.files : undefined));
    const revision = useS((s) => (s.project.state === 'ready' ? s.project.value.revision : ''));
    const author = useS((s) => s.mode === 'author');
    const given = useS((s) => s.overlay);
    const [answer, setAnswer] = useState<ViewOverlayResult | string | null>(null);
    const [tool, setTool] = useState<OverlayTool>('select');
    const [picked, setPicked] = useState<string | null>(null);
    const [newId, setNewId] = useState('');
    const [note, setNote] = useState<string | null>(null);
    const base = typeof card?.base === 'string' ? card.base : null;

    useEffect(() =>
    {
        let live = true;

        if (base && given === undefined)
        {
            actions.sceneOverlay().then((value) => { if (live) setAnswer(value); });
        }

        return () => { live = false; };
    }, [actions, base, revision, given]);

    const result = given ?? answer;
    const list = tool !== 'select' && tool !== 'move' ? TOOL_LIST[tool] : null;
    useEffect(() => { if (list) setNewId(suggestedId(files, list)); }, [list, files]);

    if (!base)
    {
        return (
            <div className={css.panel} data-testid="overlay-panel">
                <p className={css.summary}>This project makes a map of its own. An overlay project (oymap import of a shipped map) changes that map's scene: its pulsing lights, ambient sounds, destructibles, water volumes, spawn points and ladders, and adds monsters and floor items (objects.yml `scene`); its cinematics add to the map's or replace one by name.</p>
            </div>);
    }

    if (result === null)
    {
        return <div className={css.panel} data-testid="overlay-panel"><p className={css.summary}>Reading {base} ...</p></div>;
    }

    if (typeof result === 'string')
    {
        return <div className={css.panel} data-testid="overlay-panel"><p className={css.summary}>{result}</p></div>;
    }

    const summary = summariseOverlay(result);
    const frame = overlayFrame(result);
    const span = Math.max(frame[2] - frame[0], frame[3] - frame[1]);
    const scale = span / 300;
    const selected = result.things.find((thing) => thing.id === picked) ?? null;
    const edit = (gesture: OverlayGesture, label: string) =>
    {
        const op = overlayOps(files, gesture);
        if (!op)
        {
            setNote(`nothing to write for ${label}`);
            return;
        }
        setNote(null);
        void actions.edit({ ops: [op], label });
    };
    // A click on the plan: in map units (the drawing's y runs down, the map's up).
    const onPlan = (event: React.MouseEvent<SVGSVGElement>) =>
    {
        if (!author || tool === 'select')
        {
            return;
        }
        const svg = event.currentTarget;
        const matrix = svg.getScreenCTM();
        if (!matrix)
        {
            return;
        }
        const point = new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse());
        const at: [number, number] = [Math.round(point.x), Math.round(-point.y)];
        if (list)
        {
            const position: [number, number, number] = [at[0], at[1], heightNear(result.things, at, list)];
            edit({ kind: 'add', list, id: newId, position }, `add ${newId}`);
            setPicked(newId);
            setTool('select');
        }
        else if (tool === 'move' && selected && selected.origin === 'added')
        {
            edit({ kind: 'move', list: LIST_OF_KIND[selected.kind], id: selected.id, position: [at[0], at[1], selected.at[2]] }, `move ${selected.id}`);
            setTool('select');
        }
        else if (tool === 'move' && movable(selected) && selected)
        {
            edit(ladderMove(files, selected, at), `move ${selected.id}`);
            setTool('select');
        }
    };

    return (
        <div className={css.panel} data-testid="overlay-panel">
            <p className={css.summary}>
                {`An overlay of ${result.base} (${result.world}, ${result.profile}): ${summary.changes} change(s); the base map has `}
                {Object.entries(summary.baseByKind).map(([kind, count]) => `${count} ${KIND_NAMES[kind as keyof typeof KIND_NAMES]}(s)`).join(', ')}.
                {result.scene_keys.length > 0 ? ` The scene overlay writes ${result.scene_keys.join(', ')}.` : ' No scene overlay yet.'}
                {result.cinematics && result.cinematics.some((entry) => entry.state !== 'kept')
                    ? ` Cinematics: ${result.cinematics.filter((entry) => entry.state !== 'kept').map((entry) => `${entry.id} ${entry.state}`).join(', ')}.` : ''}
            </p>
            {author ? (
                <div className={css.row} data-testid="overlay-tools">
                    {TOOLS.map((name) => (
                        <button key={name} type="button" className={tool === name ? css.pickOn : css.pick} data-testid={`overlay-tool-${name}`}
                            disabled={name === 'move' && !movable(selected)} onClick={() => setTool(name)}>{TOOL_WORDS[name]}</button>))}
                    {list ? <input className={css.input} value={newId} onChange={(event) => setNewId(event.target.value)} data-testid="overlay-new-id"
                        title="The new thing's id (its number comes from ids.lock.yml when built)" /> : null}
                    <span className={css.dim}>{list ? 'click the plan where it goes' : tool === 'move' ? `click where ${selected?.id ?? 'it'} goes` : 'click a thing to change it'}</span>
                </div>) : <p className={css.dim}>Author mode changes these: pick a thing on the plan, or place a new one.</p>}
            {note ? <div className={css.dim}>{note}</div> : null}
            <div className={css.overlayGrid}>
                <svg className={`${css.plan} ${author && tool !== 'select' ? css.placing : ''}`} viewBox={`${frame[0]} ${-frame[3]} ${frame[2] - frame[0]} ${frame[3] - frame[1]}`}
                    role="img" aria-label="The overlay's things on the base map" data-testid="overlay-plan" onClick={onPlan}>
                    {result.things.flatMap((thing) => (thing.polygons ?? []).map((polygon, index) => (
                        <polygon key={`${thing.id}-${index}`} className={css.water} points={polygon.map(([px, py]) => `${px},${-py}`).join(' ')} />)))}
                    {result.things.map((thing) => (
                        <g key={thing.id} className={css[thing.state]} data-thing={thing.id}
                            onClick={(event) => { if (tool === 'select') { event.stopPropagation(); setPicked(thing.id); } }}>
                            {thing.radius && thing.state !== 'kept'
                                ? <circle cx={thing.at[0]} cy={-thing.at[1]} r={thing.radius} fill="none" strokeWidth={scale} strokeDasharray={`${scale * 4} ${scale * 3}`} /> : null}
                            {thing.id === picked ? <circle cx={thing.at[0]} cy={-thing.at[1]} r={scale * 7} fill="none" className={css.pickRing} strokeWidth={scale * 1.6} /> : null}
                            <circle cx={thing.at[0]} cy={-thing.at[1]} r={thing.state === 'kept' ? scale * 2 : scale * 3.5} fillOpacity={thing.state === 'kept' ? 0.6 : 1} stroke="none">
                                <title>{`${thing.id}: ${thing.kind}, ${thing.state} (${thing.label})`}</title>
                            </circle>
                        </g>))}
                </svg>
                <div>
                    {selected && author ? <ThingForm thing={selected} files={files} onEdit={edit} /> : null}
                    {summary.groups.filter((group) => group.state !== 'kept').map((group) => (
                        <div className={css.group} key={group.state}>
                            <div className={css.heading}>{`${group.state} (${group.things.length})`}</div>
                            {group.things.map((thing) => (
                                <div className={`${css.thing} ${thing.id === picked ? css.thingPicked : ''}`} key={thing.id} onClick={() => setPicked(thing.id)}
                                    data-testid={`overlay-thing-${thing.id}`}>
                                    <span className={css.mono}>{thing.id}</span>
                                    <span className={css.dim}>{KIND_NAMES[thing.kind]}</span>
                                    <span>{`${thing.label} at [${thing.at.join(', ')}]`}</span>
                                </div>))}
                        </div>))}
                    {result.issues.length > 0 ? (
                        <div className={css.group}>
                            <div className={css.heading}>{`issues (${result.issues.length})`}</div>
                            {result.issues.map((issue, index) => <div key={index}>{`${issue.file} ${issue.path}: ${issue.message}`}</div>)}
                        </div>) : null}
                </div>
            </div>
        </div>
    );
}
