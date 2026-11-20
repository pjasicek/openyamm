// The inspector outdoors (S5b2; S5_BROWSER_EDITOR.md 3.8, 3.18, W2, W3): over a building's or a part's generated form
// the building panel (its parts, the part's roof, the wall bay strip of every wall with the door by a click on a bay,
// the house the door enters from the house table); over a structure's the Click words (title, the lock, the steps);
// a sketch event in the event form's sections. The generated form stays below for every other word.
import { useEffect, useMemo, useState } from 'react';
import type { JsonObject, Op } from '../../../schema/rpc/generated/rpc.ts';
import type { Json, Located, Registry } from '../schema/registry.ts';
import { Field } from '../form/Fields.tsx';
import type { FormEdits } from '../form/context.ts';
import type { FoundObject } from '../model/objects.ts';
import { bayOps, bayWord, doorOf, parseHouses, partWalls, wallBays } from '../edit/bays.ts';
import type { Bay, House } from '../edit/bays.ts';
import { keysOf, segment } from '../edit/keys.ts';
import { partBox } from '../edit/outdoortools.ts';
import { ConditionRows, EffectRows } from './EventForm.tsx';
import { useActions, useS, useStudioContext } from './context.ts';
import { NumberInput, TextInput } from '../form/inputs.tsx';
import css from './OutdoorAuthor.module.css';

const ROOFS = ['hip', 'gable', 'flat', 'lean_to', 'cone', 'dome', 'none'];
const BAY_WORDS = ['wall', 'window', 'door', 'post_left', 'post_right'];
// The kinds whose click enters a house.
const HOUSE_KINDS = new Set(['building', 'sign', 'tent', 'model']);

// What the inspector shows over a sketch object's form.
export function OutdoorPanels({ found, reg, edits }: { found: FoundObject; reg: Registry; edits: FormEdits })
{
    const building = (found.list === 'structures' && found.value.kind === 'building' && !found.pointer)
        || (found.list === 'parts' && found.parentList === 'structures');
    const clickable = (found.list === 'structures' && !found.pointer) || (found.list === 'parts' && found.parentList === 'structures');
    return (
        <>
            {building ? <BuildingPanel found={found} /> : null}
            {clickable ? <ClickWords found={found} reg={reg} edits={edits} /> : null}
        </>
    );
}

function useHouses(): House[] | null
{
    const { controller } = useStudioContext();
    const key = useS((s) => s.projectKey);
    const [houses, setHouses] = useState<House[] | null>(null);
    useEffect(() =>
    {
        if (!controller || !key)
        {
            // No host (the panel gallery): the number field instead of the table.
            setHouses([]);
            return;
        }
        let live = true;
        controller.client.fetchBytes(`/walk/${encodeURIComponent(key)}/house_data.txt`).then(({ bytes }) =>
        {
            if (live)
            {
                setHouses(parseHouses(new TextDecoder().decode(bytes)));
            }
        }, () => live && setHouses([]));
        return () => { live = false; };
    }, [controller, key]);
    return houses;
}

function BuildingPanel({ found }: { found: FoundObject })
{
    const actions = useActions();
    const files = useS((s) => (s.project.state === 'ready' ? s.project.value.files : undefined));
    const id = found.id.split('/')[0];
    const box = partBox(files, found.id);
    const [chosen, setChosen] = useState<{ wall: string; bay: number } | null>(null);
    const [texture, setTexture] = useState('');
    if (!box)
    {
        return null;
    }
    const { building, part, key, size } = box;
    const parts = Array.isArray(building.parts) ? building.parts : [];
    const keys = keysOf(parts, 'parts', { field: 'id', prefix: 'part' });
    const door = doorOf(building, keys);
    const walls = partWalls(part, size);
    const send = (label: string, op: Op) => void actions.edit({ label, ops: [op] });
    const partPatch = (label: string, name: string, value: Json | undefined) => send(label, { op: 'patch', id, file: 'sketch.yml', patch: [value === undefined
        ? { op: 'remove', path: `/parts/${segment(key)}/${name}` } : { op: 'add', path: `/parts/${segment(key)}/${name}`, value: value as JsonObject }] });
    const setBay = (wallName: string, bays: Bay[], index: number, word: string) =>
    {
        const wall = walls.find((entry) => entry.name === wallName)!;
        send(`${id} ${key}: wall ${wallName} bay ${index} ${word}`, bayOps(id, building, key, part, wall, bays, index, word));
    };
    return (
        <section className={css.panel} data-testid="building-panel">
            <h4 className={css.panelTitle}>Building {id} · part {key} <span className={css.dim}>{size[0]} × {size[1]}</span></h4>
            <div className={css.row}>
                <span className={css.rowLabel}>parts</span>
                {keys.map((partKey) => (
                    <button key={partKey} type="button" className={partKey === key ? css.chipOn : css.chip} data-testid={`part-${partKey}`}
                        onClick={() => actions.select({ id: `${id}/parts/${segment(partKey)}`, file: 'sketch.yml' })}>{partKey}</button>
                ))}
                <span className={css.dim}>a new part: the Building tool (U) inside the building</span>
            </div>
            <div className={css.row} data-testid="roof-row">
                <span className={css.rowLabel}>roof</span>
                {ROOFS.map((roof) => (
                    <button key={roof} type="button" className={(part.roof ?? building.roof ?? 'hip') === roof ? css.chipOn : css.chip} data-testid={`roof-${roof}`}
                        onClick={() => partPatch(`${id} ${key}: roof ${roof}`, 'roof', roof)}>{roof}</button>
                ))}
                <span className={css.rowLabel}>pitch°</span>
                <NumberInput value={typeof part.roof_pitch === 'number' ? part.roof_pitch : undefined} placeholder="world's" width="narrow" testId="roof-pitch"
                    onCommit={(value) => partPatch(`${id} ${key}: roof pitch ${value}`, 'roof_pitch', value > 0 ? value : undefined)} />
            </div>
            {walls.map((wall) =>
            {
                const isDoorWall = door !== null && door.part === key && door.wall === wall.name;
                const { bays, written } = wallBays(part, wall, isDoorWall, isDoorWall ? door?.bay : undefined);
                return (
                    <div key={wall.name} className={css.wall} data-testid={`wall-${wall.name}`}>
                        <div className={css.wallHead}>
                            <span className={css.wallName}>wall {wall.name}</span>
                            <span className={css.dim}>{wall.length} long · {bays.length} bays{written ? '' : ' (laid by rule)'}</span>
                        </div>
                        <div className={css.strip} role="group" aria-label={`wall ${wall.name}'s bays`}>
                            {bays.map((bay, index) =>
                            {
                                const word = bayWord(bay);
                                const on = chosen?.wall === wall.name && chosen.bay === index;
                                const style = on ? css.bayOn : word === 'door' ? css.bayDoor : word === 'window' ? css.bayWindow : word.startsWith('post') ? css.bayPost : css.bay;
                                return (
                                    <button key={index} type="button" className={style} title={`bay ${index}: ${word} (click to change it)`} data-testid={`bay-${wall.name}-${index}`}
                                        onClick={() => setChosen(on ? null : { wall: wall.name, bay: index })}>{word === 'post_left' || word === 'post_right' ? '|' : word.slice(0, 6)}</button>
                                );
                            })}
                        </div>
                        {chosen?.wall === wall.name ? (
                            <div className={css.row} data-testid="bay-roles">
                                <span className={css.rowLabel}>bay {chosen.bay}</span>
                                {BAY_WORDS.map((word) => (
                                    <button key={word} type="button" className={bayWord(bays[chosen.bay]) === word ? css.chipOn : css.chip} data-testid={`bay-role-${word}`}
                                        onClick={() => { setBay(wall.name, bays, chosen.bay, word); setChosen(null); }}>{word === 'door' ? 'door here' : word}</button>
                                ))}
                                <TextInput value={texture} onCommit={setTexture} placeholder="a texture's name" testId="bay-texture" />
                                <button type="button" className={css.chip} disabled={!texture.trim()} onClick={() => { setBay(wall.name, bays, chosen.bay, texture.trim()); setChosen(null); }}>use it</button>
                            </div>
                        ) : null}
                    </div>
                );
            })}
            <DoorHouse id={id} building={building} door={door} />
        </section>
    );
}

// Where the door is and the house it enters (the house table, searched), or another map (`into`, in the form).
function DoorHouse({ id, building, door }: { id: string; building: JsonObject; door: { part: string; wall: string; bay?: number } | null })
{
    const actions = useActions();
    const houses = useHouses();
    const [query, setQuery] = useState('');
    const house = typeof building.house === 'number' ? building.house : null;
    const shown = useMemo(() =>
    {
        const words = query.toLowerCase().split(/\s+/).filter(Boolean);
        return (houses ?? []).filter((entry) => words.every((word) => `${entry.number} ${entry.type} ${entry.name}`.toLowerCase().includes(word))).slice(0, 80);
    }, [houses, query]);
    const current = houses?.find((entry) => entry.number === house);
    const set = (value: number | null) => void actions.edit({ label: value === null ? `${id}: no house` : `${id} enters house ${value}`,
        ops: [{ op: 'set', id, file: 'sketch.yml', fields: { house: value } }] });
    return (
        <div className={css.wall} data-testid="door-house">
            <div className={css.wallHead}>
                <span className={css.wallName}>door</span>
                <span className={css.dim}>{door ? `part ${door.part}, wall ${door.wall}${door.bay !== undefined ? `, bay ${door.bay}` : ' (its middle)'}` : 'none'}</span>
            </div>
            <div className={css.row}>
                <span className={css.rowLabel}>house</span>
                <b>{house === null ? 'none' : `${house}${current ? ` ${current.name} (${current.type})` : ''}`}</b>
                {house !== null ? <button type="button" className={css.chip} onClick={() => set(null)}>clear</button> : null}
            </div>
            {houses === null ? <p className={css.dim}>Reading the house table…</p> : houses.length === 0 ? (
                <div className={css.row}>
                    <span className={css.dim}>The host gives no house table: its number</span>
                    <NumberInput value={house ?? undefined} width="narrow" integer min={1} testId="house-number" onCommit={(value) => set(value)} />
                </div>
            ) : (
                <>
                    <input className={css.search} value={query} onChange={(event) => setQuery(event.target.value)} placeholder="search the houses: tavern, temple, 23"
                        data-testid="house-search" />
                    <div className={css.houses} data-testid="house-list">
                        {shown.map((entry) => (
                            <button key={entry.number} type="button" className={entry.number === house ? css.houseOn : css.house} data-testid={`house-${entry.number}`}
                                onClick={() => set(entry.number)}>
                                <span className={css.houseNumber}>{entry.number}</span><span>{entry.name}</span><span className={css.dim}>{entry.type}</span>
                            </button>
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}

// The schema of a property of the object's own schema (structures' items, a part's $def).
function propLoc(reg: Registry, found: FoundObject, name: string): Located | null
{
    const owner = found.list === 'parts' ? reg.at('sketch.schema.json', '#/$defs/part') : reg.at('sketch.schema.json', '#/properties/structures/items');
    const resolved = reg.resolve(owner);
    return resolved.node.properties?.[name] ? reg.child(resolved, 'properties', name) : null;
}

// What a click on a structure (or a part) does: its title, the house it enters (buildings, signs, tents), the
// lock and the steps; the event form's rows (W3, W4).
function ClickWords({ found, reg, edits }: { found: FoundObject; reg: Registry; edits: FormEdits })
{
    const value = found.value as JsonObject;
    const field = (name: string, label: string) =>
    {
        const loc = propLoc(reg, found, name);
        return loc ? <Field key={name} loc={loc} value={value[name] as Json | undefined} path={[name]} label={label} removable={value[name] !== undefined} /> : null;
    };
    const kind = typeof value.kind === 'string' ? value.kind : found.list === 'parts' ? 'part' : '';
    return (
        <section className={css.panel} data-testid="click-words">
            <h4 className={css.panelTitle}>Click <span className={css.dim}>what using it does (the event form's words)</span></h4>
            {field('title', 'says (title)')}
            {HOUSE_KINDS.has(kind) && kind !== 'building' ? field('house', 'enters house') : null}
            <h5 className={css.dim}>Lock</h5>
            <ConditionRows reg={reg} edits={edits} condition={value.condition} />
            {value.condition !== undefined ? field('locked_text', 'when locked, say') : null}
            {field('once', 'only the first time')}
            <h5 className={css.dim}>Does</h5>
            <EffectRows reg={reg} edits={edits} list="effects" steps={value.effects} />
            {value.condition !== undefined || value.else_effects !== undefined ? <EffectRows reg={reg} edits={edits} list="else_effects" steps={value.else_effects} /> : null}
        </section>
    );
}

// A sketch event (nobody clicks it: on entering, by the clock) in the event form's sections.
export function OutdoorEventForm({ found, reg, edits }: { found: FoundObject; reg: Registry; edits: FormEdits })
{
    const event = found.value as JsonObject;
    const loc = reg.resolve(reg.at('sketch.schema.json', '#/properties/events/items'));
    const field = (name: string, label: string) => (loc.node.properties?.[name]
        ? <Field key={name} loc={reg.child(loc, 'properties', name)} value={event[name] as Json | undefined} path={[name]} label={label} removable={event[name] !== undefined && name !== 'trigger'} />
        : null);
    const trigger = typeof event.trigger === 'string' ? event.trigger : 'load';
    return (
        <div className={css.panel} data-testid="event-form">
            <h4 className={css.panelTitle}>Event {found.id}</h4>
            <h5 className={css.dim}>Runs on</h5>
            {field('trigger', 'trigger')}
            {trigger === 'timer' ? <>{field('every', 'every (seconds)')}{field('when_flying', 'only while flying')}</> : null}
            {trigger === 'daily' ? field('hour', 'at the hour') : null}
            <h5 className={css.dim}>Lock</h5>
            <ConditionRows reg={reg} edits={edits} condition={event.condition} />
            {event.condition !== undefined ? field('locked_text', 'when locked, say') : null}
            {field('once', 'only the first time')}
            <h5 className={css.dim}>Does</h5>
            <EffectRows reg={reg} edits={edits} list="effects" steps={event.effects} />
            {event.condition !== undefined || event.else_effects !== undefined ? <EffectRows reg={reg} edits={edits} list="else_effects" steps={event.else_effects} /> : null}
        </div>
    );
}
