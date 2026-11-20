// The generated inspector (S5_BROWSER_EDITOR.md 3.8): one component per widget of plan.ts, on Base UI primitives.
// Read only in Review mode; in Author mode (S5b1) every field edits: numbers take expressions and show their unit,
// ids are picked from the project's ids of the kinds the schema allows (x-id-kinds), keyed sub-lists show rows named
// by their key (add, remove, duplicate, reorder, rename the key), absent fields come behind "+ add field" and show
// the core's effective value greyed ("not written"). Typing commits on Enter or on leaving the field.
// Closed sections are not mounted (Base UI Collapsible keeps a closed panel out of the tree).
import { useMemo } from 'react';
import { Collapsible } from '@base-ui/react/collapsible';
import { Popover } from '@base-ui/react/popover';
import { Menu } from '@base-ui/react/menu';
import { Select } from '@base-ui/react/select';
import { Combobox } from '@base-ui/react/combobox';
import { Switch } from '@base-ui/react/switch';
import type { Json, Located } from '../schema/registry.ts';
import { classify, humanise, makeDefault, planObject, UNIT_LABELS } from './plan.ts';
import type { FieldEntry, Geom, Widget } from './plan.ts';
import { unitFor, useForm } from './context.ts';
import type { Path } from './context.ts';
import { NumberInput, TextInput } from './inputs.tsx';
import { keysOf } from '../edit/keys.ts';
import type { KeyedList } from '../edit/keys.ts';
import css from './Fields.module.css';

const BLOCK = new Set(['object', 'list', 'map', 'geom', 'bespoke']);

function Help({ text }: { text: string })
{
    if (!text)
    {
        return null;
    }
    return (
        <Popover.Root>
            <Popover.Trigger openOnHover delay={250} className={css.help} aria-label="Help">?</Popover.Trigger>
            <Popover.Portal>
                <Popover.Positioner side="left" sideOffset={6} className={css.positioner}>
                    <Popover.Popup className={css.helpPopup}>{text}</Popover.Popup>
                </Popover.Positioner>
            </Popover.Portal>
        </Popover.Root>
    );
}

interface FieldProps
{
    loc: Located;
    value: Json | undefined;
    path: Path;
    label: string;
    description?: string;
    required?: boolean;
    // An optional field written in the object: offer to remove it.
    removable?: boolean;
    // The core's effective value of an absent field ("not written").
    effective?: { value: Json; source: string; from?: string };
}

function RemoveButton({ path }: { path: Path })
{
    const { edits } = useForm();
    if (!edits)
    {
        return null;
    }
    return <button type="button" className={css.icon} title="Remove this field (its default applies again)" onClick={() => edits.field(path, undefined)}>×</button>;
}

// One property: a row for scalars, a section for objects, lists, maps and geometry.
export function Field({ loc, value, path, label, description, required, removable, effective }: FieldProps)
{
    const { reg } = useForm();
    const widget = useMemo(() => classify(reg, loc), [reg, loc.file, loc.ptr]);
    const desc = description ?? reg.resolve(loc).node.description ?? '';
    const missing = value === undefined && required;
    const tools = removable ? <RemoveButton path={path} /> : null;
    if (widget.kind === 'union')
    {
        const branch = widget.union.branches.find((b) => value !== undefined && b.test(value)) ?? widget.union.branches[0];
        const inner = classify(reg, branch.loc);
        const switcher = <UnionSwitch widget={widget} active={branch.label} path={path} value={value} />;
        if (BLOCK.has(inner.kind) || inner.kind === 'tuple')
        {
            return (
                <Block label={label} desc={desc} badge={branch.label} tools={<>{switcher}{tools}</>} testId={`block-${path.join('.')}`}>
                    <Control widget={inner} loc={branch.loc} value={value} path={path} effective={effective} />
                </Block>
            );
        }
        return <Row label={label} desc={desc} missing={missing} tools={tools}><span className={css.unionInline}>{switcher}<Control widget={inner} loc={branch.loc} value={value} path={path} effective={effective} /></span></Row>;
    }
    if (BLOCK.has(widget.kind) && !(widget.kind === 'geom' && !widget.many))
    {
        return (
            <Block label={label} desc={desc} badge={badgeFor(widget, value)} tools={tools} testId={`block-${path.join('.')}`}>
                <Control widget={widget} loc={loc} value={value} path={path} effective={effective} />
            </Block>
        );
    }
    return <Row label={label} desc={desc} missing={missing} tools={tools} effective={value === undefined ? effective : undefined}>
        <Control widget={widget} loc={loc} value={value} path={path} effective={effective} />
    </Row>;
}

// A union told apart by JSON type or by a named branch: which branch, and a switch to another (its default value).
function UnionSwitch({ widget, active, path, value }: { widget: Extract<Widget, { kind: 'union' }>; active: string; path: Path; value: Json | undefined })
{
    const { reg, edits } = useForm();
    if (!edits || widget.union.branches.length < 2 || widget.union.mode === 'shape')
    {
        return null;
    }
    return (
        <Select.Root value={active} onValueChange={(label) =>
        {
            const branch = widget.union.branches.find((b) => b.label === label);
            if (branch && label !== active)
            {
                edits.field(path, makeDefault(reg, branch.loc));
            }
        }}>
            <Select.Trigger className={css.select} title={value === undefined ? 'not written' : 'the form of this value'}><Select.Value /><Select.Icon className={css.selectIcon}>▾</Select.Icon></Select.Trigger>
            <Select.Portal>
                <Select.Positioner className={css.positioner} sideOffset={4}>
                    <Select.Popup className={css.popup}>
                        <Select.List>
                            {widget.union.branches.map((b) => <Select.Item key={b.label} value={b.label} className={css.item}><Select.ItemText>{b.label}</Select.ItemText></Select.Item>)}
                        </Select.List>
                    </Select.Popup>
                </Select.Positioner>
            </Select.Portal>
        </Select.Root>
    );
}

function Row({ label, desc, missing, tools, effective, children }: { label: string; desc: string; missing?: boolean; tools?: React.ReactNode; effective?: { source: string; from?: string }; children: React.ReactNode })
{
    return (
        <div className={`${css.row} ${effective ? css.notWritten : ''}`} data-missing={missing || undefined}>
            <span className={css.label} title={effective ? `${label}: not written (${effective.source}${effective.from ? `, from ${effective.from}` : ''})` : label}>{label}</span>
            <span className={css.control}>{children}</span>
            <span className={css.tools}>{tools}<Help text={desc} /></span>
        </div>
    );
}

function badgeFor(widget: Widget, value: Json | undefined): string | undefined
{
    if (widget.kind === 'geom')
    {
        return `${widget.geom.shape} · ${typeof widget.geom.space === 'string' ? widget.geom.space : 'per kind'}`;
    }
    if (widget.kind === 'list')
    {
        return `${Array.isArray(value) ? value.length : 0} rows`;
    }
    if (widget.kind === 'bespoke')
    {
        return `bespoke: ${widget.name}`;
    }
    return undefined;
}

function Block({ label, desc, badge, tools, children, testId }: { label: string; desc: string; badge?: string; tools?: React.ReactNode; children: React.ReactNode; testId?: string })
{
    const { expandAll } = useForm();
    return (
        <Collapsible.Root defaultOpen={expandAll || undefined} className={css.block}>
            <div className={css.blockHead}>
                <Collapsible.Trigger className={css.blockTrigger} data-testid={testId}>
                    <span className={css.chevron} aria-hidden>▸</span>{label}
                </Collapsible.Trigger>
                {badge ? <span className={css.badge}>{badge}</span> : null}
                <span className={css.tools}>{tools}<Help text={desc} /></span>
            </div>
            <Collapsible.Panel className={css.blockBody}>{children}</Collapsible.Panel>
        </Collapsible.Root>
    );
}

function effectiveText(effective: { value: Json } | undefined): string | undefined
{
    if (!effective)
    {
        return undefined;
    }
    const value = effective.value;
    // A surface reads as its texture and size (t1w11a 128 × 256).
    if (value && typeof value === 'object' && !Array.isArray(value) && typeof value.texture === 'string')
    {
        const size = Array.isArray(value.size) ? ` ${value.size.join(' × ')}` : '';
        const rest = Object.entries(value).filter(([k]) => k !== 'texture' && k !== 'size').map(([k, v]) => `${k} ${JSON.stringify(v)}`);
        return `${value.texture}${size}${rest.length ? ` · ${rest.join(' · ')}` : ''}`;
    }
    return typeof value === 'object' ? JSON.stringify(value) : String(value);
}

function Control({ widget, loc, value, path, effective }: { widget: Widget; loc: Located; value: Json | undefined; path: Path; effective?: { value: Json; source: string; from?: string } })
{
    const { kind, edits } = useForm();
    switch (widget.kind)
    {
    case 'text':
        if (edits)
        {
            return (
                <span className={css.withSuffix}>
                    {widget.multiline
                        ? <TextArea value={typeof value === 'string' ? value : undefined} onCommit={(text) => edits.field(path, text)} testId={`field-${path.join('.')}`} />
                        : <TextInput value={typeof value === 'string' ? value : undefined} effective={effectiveText(effective)} pattern={widget.pattern} onCommit={(text) => edits.field(path, text)} testId={`field-${path.join('.')}`} />}
                    {widget.table ? <span className={css.table}>{widget.table}</span> : null}
                </span>
            );
        }
        return typeof value === 'string' && value.length > 48
            ? <span className={css.longText}>{value}</span>
            : <span className={css.value}>{value === undefined ? effectiveOrDash(effective) : String(value)}{widget.table ? <span className={css.table}> {widget.table}</span> : null}</span>;
    case 'number':
    {
        const unit = unitFor(widget.unit, kind);
        const suffix = unit && UNIT_LABELS[unit] ? <span className={css.unit}>{UNIT_LABELS[unit]}</span> : null;
        if (edits)
        {
            return (
                <span className={css.withSuffix}>
                    <NumberInput value={typeof value === 'number' ? value : undefined} effective={effectiveText(effective)} integer={widget.integer} min={widget.min} max={widget.max}
                        onCommit={(number) => edits.field(path, number)} testId={`field-${path.join('.')}`} />
                    {suffix}
                </span>
            );
        }
        return <span className={css.value}>{typeof value === 'number' ? String(value) : effectiveOrDash(effective)}{suffix ? <> {suffix}</> : null}</span>;
    }
    case 'boolean':
        if (edits)
        {
            return (
                <Switch.Root className={css.switch} checked={value === true || (value === undefined && effective?.value === true)}
                    onCheckedChange={(checked) => edits.field(path, checked)} data-testid={`field-${path.join('.')}`}>
                    <Switch.Thumb className={css.thumb} />
                </Switch.Root>
            );
        }
        return <span className={css.value}>{value === true ? 'yes' : value === false ? 'no' : effectiveOrDash(effective)}</span>;
    case 'enum':
        if (edits)
        {
            return <EnumPicker options={widget.options} value={value} effective={effective} onPick={(option) => edits.field(path, option)} testId={`field-${path.join('.')}`} />;
        }
        return <span className={css.value}>{value === undefined ? effective ? effectiveOrDash(effective) : '(default)' : String(value)}</span>;
    case 'const':
        return <span className={css.const}>{String(widget.value)}</span>;
    case 'id':
        return edits && !widget.own ? <IdPicker value={value} kinds={widget.kinds} effective={effectiveText(effective)} onPick={(id) => edits.field(path, id)} testId={`field-${path.join('.')}`} /> : <IdValue value={value} />;
    case 'tuple':
        if (edits)
        {
            const values = Array.isArray(value) ? value : [];
            return (
                <span className={css.tuple}>
                    {widget.items.map((_, i) => (
                        <NumberInput key={i} value={typeof values[i] === 'number' ? (values[i] as number) : undefined} width="narrow" testId={`field-${path.join('.')}.${i}`}
                            onCommit={(number) => edits.field(path, Array.isArray(value) ? [...values.slice(0, i), number, ...values.slice(i + 1)] : widget.items.map((__, j) => (j === i ? number : 0)))} />
                    ))}
                </span>
            );
        }
        return <span className={css.value}>{Array.isArray(value) ? `[${value.map((v) => JSON.stringify(v)).join(', ')}]` : '—'}</span>;
    case 'geom':
        return <GeomValue value={value} geom={widget.geom} path={path} />;
    case 'list':
        return <ListValue value={value} path={path} widget={widget} />;
    case 'map':
    {
        const obj = (value && typeof value === 'object' && !Array.isArray(value) ? value : {}) as Record<string, Json>;
        return (
            <div className={css.list}>
                {Object.entries(obj).map(([k, v]) => <Field key={k} loc={widget.value} value={v} path={[...path, k]} label={k} description="" removable={Boolean(edits)} />)}
            </div>
        );
    }
    case 'object':
        return <ObjectForm loc={loc} value={(value ?? {}) as Record<string, Json>} path={path} />;
    case 'bespoke':
        return (
            <div className={css.bespoke}>
                <div className={css.dim}>The {widget.name} are edited in the event form (switch off “every word”).</div>
                {(Array.isArray(value) ? value : []).map((s, i) => <code key={i} className={css.raw}>{JSON.stringify(s)}</code>)}
            </div>
        );
    case 'raw':
        if (edits)
        {
            return <RawInput value={value} onCommit={(parsed) => edits.field(path, parsed)} />;
        }
        return <code className={css.raw} title={widget.reason}>{JSON.stringify(value)}</code>;
    default:
        return null;
    }
}

function effectiveOrDash(effective: { value: Json; source: string; from?: string } | undefined): React.ReactNode
{
    if (!effective)
    {
        return '—';
    }
    return <span className={css.effective} title={`not written: ${effective.source}${effective.from ? ` (${effective.from})` : ''}`}>{effectiveText(effective)}</span>;
}

function TextArea({ value, onCommit, testId }: { value: string | undefined; onCommit: (text: string) => void; testId?: string })
{
    return (
        <textarea className={css.textarea} defaultValue={value ?? ''} rows={3} key={value ?? ''} data-testid={testId}
            onBlur={(event) => event.target.value !== (value ?? '') && onCommit(event.target.value)}
            onKeyDown={(event) =>
            {
                if (event.key === 'Enter' && (event.ctrlKey || event.metaKey))
                {
                    (event.target as HTMLTextAreaElement).blur();
                }
            }} />
    );
}

// A value the form has no widget for: edited as JSON text.
function RawInput({ value, onCommit }: { value: Json | undefined; onCommit: (value: Json) => void })
{
    return (
        <TextInput value={value === undefined ? undefined : JSON.stringify(value)} title="JSON" onCommit={(text) =>
        {
            try
            {
                onCommit(JSON.parse(text) as Json);
            }
            catch
            {
                // Left as typed: not JSON.
            }
        }} />
    );
}

function EnumPicker({ options, value, effective, onPick, testId }: { options: Json[]; value: Json | undefined; effective?: { value: Json }; onPick: (value: Json) => void; testId?: string })
{
    const shown = value !== undefined ? String(value) : null;
    return (
        <Select.Root value={shown} onValueChange={(picked) =>
        {
            const option = options.find((entry) => String(entry) === picked);
            if (option !== undefined && picked !== shown)
            {
                onPick(option);
            }
        }}>
            <Select.Trigger className={css.select} data-testid={testId}>
                <Select.Value placeholder={effective ? `${String(effective.value)} (not written)` : '(default)'} />
                <Select.Icon className={css.selectIcon}>▾</Select.Icon>
            </Select.Trigger>
            <Select.Portal>
                <Select.Positioner className={css.positioner} sideOffset={4}>
                    <Select.Popup className={css.popup}>
                        <Select.List>
                            {options.map((option) => (
                                <Select.Item key={String(option)} value={String(option)} className={css.item}><Select.ItemText>{String(option)}</Select.ItemText></Select.Item>
                            ))}
                        </Select.List>
                    </Select.Popup>
                </Select.Positioner>
            </Select.Portal>
        </Select.Root>
    );
}

// An id field: the project's ids of the kinds the schema allows (x-id-kinds; every id without it), typed to filter.
function IdPicker({ value, kinds, effective, onPick, testId }: { value: Json | undefined; kinds?: string[]; effective?: string; onPick: (id: string) => void; testId?: string })
{
    const { ids, onSelectId } = useForm();
    const items = useMemo(() => [...ids].filter((id) => !id.includes('/') && (!kinds || kinds.some((kind) => id.startsWith(`${kind}:`)))).sort(), [ids, kinds]);
    const current = typeof value === 'string' ? value : null;
    return (
        <span className={css.withSuffix}>
            <Combobox.Root items={items} value={current} onValueChange={(picked) => typeof picked === 'string' && picked !== current && onPick(picked)}>
                <span className={css.comboGroup}>
                    <Combobox.Input className={css.input} data-effective={current === null && effective ? '' : undefined} data-testid={testId}
                        placeholder={current === null && effective ? `${effective} (not written)` : kinds ? kinds.map((kind) => `${kind}:…`).join(' / ') : 'kind:name'} />
                    <Combobox.Trigger className={css.comboTrigger} aria-label="Pick">▾</Combobox.Trigger>
                </span>
                <Combobox.Portal>
                    <Combobox.Positioner className={css.positioner} sideOffset={4}>
                        <Combobox.Popup className={css.popup}>
                            <Combobox.Empty className={css.empty}>No id of {kinds ? kinds.join(', ') : 'any kind'} matches.</Combobox.Empty>
                            <Combobox.List>
                                {(item: string) => <Combobox.Item key={item} value={item} className={css.item}>{item}</Combobox.Item>}
                            </Combobox.List>
                        </Combobox.Popup>
                    </Combobox.Positioner>
                </Combobox.Portal>
            </Combobox.Root>
            {current && ids.has(current) ? <button type="button" className={css.icon} onClick={() => onSelectId(current)} title={`select ${current}`}>→</button> : null}
        </span>
    );
}

function IdValue({ value }: { value: Json | undefined })
{
    const { ids, onSelectId } = useForm();
    if (typeof value !== 'string')
    {
        return <span className={css.value}>—</span>;
    }
    return ids.has(value)
        ? <button type="button" className={css.idLink} onClick={() => onSelectId(value)} title="select">{value}</button>
        : <span className={css.value}>{value}</span>;
}

function points(value: Json | undefined): number[][]
{
    if (!Array.isArray(value))
    {
        return [];
    }
    if (value.length > 0 && typeof value[0] === 'number')
    {
        return [value as number[]];
    }
    return (value as Json[]).flatMap((v) => (Array.isArray(v) && typeof v[0] === 'number' ? [v as number[]] : Array.isArray(v) ? points(v) : []));
}

function GeomValue({ value, geom, path }: { value: Json | undefined; geom: Geom; path: Path })
{
    const { edits } = useForm();
    const pts = points(value);
    const xs = pts.map((p) => p[0]);
    const ys = pts.map((p) => p[1]);
    const minX = Math.min(...xs);
    const minY = Math.min(...ys);
    const w = Math.max(...xs) - minX || 1;
    const h = Math.max(...ys) - minY || 1;
    const many = pts.length > 1 && geom.shape !== 'size';
    const side = Math.max(w, h);
    // A list of points (an outline) whose items are points themselves; a single point is edited in place.
    const single = Array.isArray(value) && value.length > 0 && typeof value[0] === 'number';
    return (
        <div className={css.geom}>
            <div className={css.geomHead}>
                {many ? (
                    <svg className={css.geomSvg} viewBox="-4 -4 108 108" aria-hidden>
                        <polyline
                            points={pts.map((p) => `${((p[0] - minX) / side) * 100},${100 - ((p[1] - minY) / side) * 100}`).join(' ')}
                            className={geom.shape === 'polygon' ? css.geomPoly : css.geomLine}
                        />
                    </svg>
                ) : null}
                {edits && (single || value === undefined) && !many ? (
                    <span className={css.tuple}>
                        {[0, 1, ...(geom.shape === 'point3' ? [2] : [])].map((i) => (
                            <NumberInput key={i} width="narrow" value={typeof (pts[0] ?? [])[i] === 'number' ? pts[0][i] : undefined}
                                onCommit={(number) => edits.field(path, [0, 1, ...(geom.shape === 'point3' ? [2] : [])].map((j) => (j === i ? number : (pts[0]?.[j] ?? 0))))} />
                        ))}
                    </span>
                ) : (
                    <span className={css.geomText}>
                        {geom.shape === 'size' ? `${pts[0]?.join(' × ') ?? '—'}` : many ? `${pts.length} points, ${Math.round(w)} × ${Math.round(h)}` : pts[0] ? `[${pts[0].join(', ')}]` : '—'}
                        <span className={css.dim}> in {typeof geom.space === 'string' ? geom.space : 'per-kind'} space{edits && many ? ' · drag its handles on the plan' : ''}</span>
                    </span>
                )}
            </div>
            {many ? (
                <Collapsible.Root className={css.geomPoints}>
                    <Collapsible.Trigger className={css.linkButton}>points</Collapsible.Trigger>
                    <Collapsible.Panel>
                        <div className={css.points}>
                            {pts.map((p, i) => (
                                edits && Array.isArray(value) && Array.isArray(value[i]) ? (
                                    <PointRow key={i} index={i} point={p} onCommit={(point) => edits.field([...path, i], point)} onRemove={pts.length > 3 ? () => edits.field([...path, i], undefined) : undefined} />
                                ) : (
                                    <div key={i} className={css.pointRow}>
                                        <span className={css.dim}>{i}</span>
                                        <span className={css.value}>[{p.join(', ')}]</span>
                                    </div>
                                )
                            ))}
                        </div>
                    </Collapsible.Panel>
                </Collapsible.Root>
            ) : null}
        </div>
    );
}

function PointRow({ index, point, onCommit, onRemove }: { index: number; point: number[]; onCommit: (point: number[]) => void; onRemove?: () => void })
{
    return (
        <>
            <span className={css.dim}>{index}{onRemove ? <button type="button" className={css.icon} onClick={onRemove} title="Remove this point">×</button> : null}</span>
            <NumberInput value={point[0]} width="narrow" onCommit={(x) => onCommit([x, ...point.slice(1)])} />
            <NumberInput value={point[1]} width="narrow" onCommit={(y) => onCommit([point[0], y, ...point.slice(2)])} />
        </>
    );
}

function rowKey(row: Json, key: string | false | undefined, index: number): string
{
    for (const candidate of [typeof key === 'string' && key !== '#' ? key : undefined, 'id', 'wall'])
    {
        if (candidate && row && typeof row === 'object' && !Array.isArray(row))
        {
            const k = (row as Record<string, Json>)[candidate];
            if (k !== undefined)
            {
                return String(k);
            }
        }
    }
    return `#${index}`;
}

function summary(row: Json): string
{
    if (!row || typeof row !== 'object' || Array.isArray(row))
    {
        return JSON.stringify(row);
    }
    return Object.entries(row as Record<string, Json>)
        .filter(([k, v]) => k !== 'id' && k !== 'key' && (typeof v !== 'object' || v === null))
        .slice(0, 4)
        .map(([k, v]) => `${humanise(k)} ${String(v)}`)
        .join(' · ');
}

function RowTools({ path, index, count }: { path: Path; index: number; count: number })
{
    const { edits } = useForm();
    if (!edits)
    {
        return null;
    }
    return (
        <span className={css.rowTools}>
            <button type="button" className={css.icon} disabled={index === 0} onClick={() => edits.row(path, index, 'up')} title="Move up">↑</button>
            <button type="button" className={css.icon} disabled={index === count - 1} onClick={() => edits.row(path, index, 'down')} title="Move down">↓</button>
            <button type="button" className={css.icon} onClick={() => edits.row(path, index, 'duplicate')} title="Duplicate (a new key)">⧉</button>
            <button type="button" className={css.icon} onClick={() => edits.row(path, index, 'remove')} title="Remove">×</button>
        </span>
    );
}

function ListValue({ value, path, widget }: { value: Json | undefined; path: Path; widget: Extract<Widget, { kind: 'list' }> })
{
    const { reg, expandAll, edits } = useForm();
    const rows = Array.isArray(value) ? value : [];
    const name = String([...path].reverse().find((step) => typeof step === 'string') ?? '');
    // A keyed list's rows are named by their key, as the core reads a missing one (2.6 item 2): the schema's x-key and
    // x-key-prefix at the list's place (a list of objects with ids and no prefix shows each row's id).
    const keyed: KeyedList | undefined = typeof widget.key === 'string' && widget.key !== '#' && (widget.key !== 'id' || widget.prefix)
        ? { field: widget.key, ...(widget.prefix ? { prefix: widget.prefix } : {}) } : undefined;
    const keys = keyed ? keysOf(rows as never[], name, keyed) : null;
    const add = edits ? (
        <button type="button" className={`${css.textButton} ${css.addRow}`} onClick={() => edits.addRow(path, makeDefault(reg, widget.item))} data-testid={`add-row-${name}`}>+ add {humanise(name).replace(/s$/, '') || 'row'}</button>
    ) : null;
    if (!widget.ofObjects)
    {
        return (
            <div className={css.list}>
                {rows.map((row, i) => <Field key={i} loc={widget.item} value={row} path={[...path, i]} label={`${i}`} description="" removable={Boolean(edits)} />)}
                {add}
            </div>
        );
    }
    return (
        <div className={css.list}>
            {rows.map((row, i) => (
                <Collapsible.Root key={keys ? keys[i] : i} className={css.listRow} defaultOpen={expandAll || undefined}>
                    <div className={css.listHead}>
                        <Collapsible.Trigger className={css.blockTrigger}>
                            <span className={css.chevron} aria-hidden>▸</span>
                            {keys && keyed?.field === 'key' && edits ? null : <span className={css.key}>{keys ? keys[i] : rowKey(row, widget.key, i)}</span>}
                            <span className={css.summary}>{summary(row)}</span>
                        </Collapsible.Trigger>
                        {keys && keyed?.field === 'key' && edits ? (
                            <KeyInput value={keys[i]} onCommit={(to) => edits.renameKey(path, i, to)} />
                        ) : null}
                        <RowTools path={path} index={i} count={rows.length} />
                    </div>
                    <Collapsible.Panel className={css.blockBody}>
                        <Control widget={classify(reg, widget.item)} loc={widget.item} value={row} path={[...path, i]} />
                    </Collapsible.Panel>
                </Collapsible.Root>
            ))}
            {add}
        </div>
    );
}

function KeyInput({ value, onCommit }: { value: string; onCommit: (to: string) => void })
{
    return (
        <input className={css.keyInput} defaultValue={value} key={value} title="The row's key: rename it (pins and selections follow)"
            onBlur={(event) => event.target.value !== value && /^[a-z0-9][a-z0-9_]*$/.test(event.target.value) && onCommit(event.target.value)}
            onKeyDown={(event) =>
            {
                if (event.key === 'Enter')
                {
                    (event.target as HTMLInputElement).blur();
                }
                else if (event.key === 'Escape')
                {
                    (event.target as HTMLInputElement).value = value;
                    (event.target as HTMLInputElement).blur();
                }
            }} />
    );
}

// "+ add field": the words the object does not write, each with its description.
function AddField({ fields, path }: { fields: FieldEntry[]; path: Path })
{
    const { reg, edits, resolved } = useForm();
    if (!edits || fields.length === 0)
    {
        return null;
    }
    return (
        <Menu.Root>
            <Menu.Trigger className={css.addField} data-testid="add-field">+ add field ({fields.length})</Menu.Trigger>
            <Menu.Portal>
                <Menu.Positioner className={css.positioner} sideOffset={4} align="start">
                    <Menu.Popup className={`${css.popup} ${css.addMenu}`}>
                        {fields.map((field) => (
                            <Menu.Item key={field.name} className={css.item} onClick={() =>
                            {
                                // The effective value when the core gives one at this level, else the schema's.
                                const effective = path.length === 0 ? resolved?.[field.name]?.value : undefined;
                                edits.field([...path, field.name], effective !== undefined ? effective : makeDefault(reg, field.loc));
                            }}>
                                <span className={css.addName}>{humanise(field.name)}</span>
                                {field.description ? <span className={css.addDesc}>{field.description.length > 140 ? `${field.description.slice(0, 140)}…` : field.description}</span> : null}
                            </Menu.Item>
                        ))}
                    </Menu.Popup>
                </Menu.Positioner>
            </Menu.Portal>
        </Menu.Root>
    );
}

// An object: its kind, its sections, the words it does not write behind "+ add field", and (at the top) the
// effective values of absent words the core resolves, greyed.
export function ObjectForm({ loc, value, path }: { loc: Located; value: Record<string, Json>; path: Path })
{
    const { reg, edits, resolved } = useForm();
    const plan = planObject(reg, loc, value);
    const top = path.length === 0;
    const fieldOf = (f: FieldEntry) => (top && edits?.rename && f.name === edits.rename.field && typeof value[f.name] === 'string' ? (
        <Row key={f.name} label={f.name} desc={f.name === 'id'
            ? 'The object\'s id. Renaming it changes every reference to it in the project, its engine number in the id lock and the pins on it.'
            : 'The key that names this row in its list. Renaming it moves the pins and selections on it along.'}>
            <TextInput value={String(value[f.name])} pattern={f.name === 'id' ? '^[a-z][a-z0-9_]*:[a-z0-9][a-z0-9_]*$' : '^[a-z0-9][a-z0-9_]*$'} testId={`rename-${f.name}`}
                onCommit={(to) => to !== value[f.name] && edits.rename?.to(to)} title="Rename: what names it follows" />
        </Row>
    ) : (
        <Field key={f.name} loc={f.loc} value={value[f.name]} path={[...path, f.name]} label={humanise(f.name)} description={f.description}
            required={f.required} removable={Boolean(edits) && !f.required && f.name in value && f.name !== 'id' && f.name !== 'key'}
            effective={top && !(f.name in value) ? resolved?.[f.name] : undefined} />
    ));
    // Absent words the core gives a value to: shown greyed under their own heading ("not written").
    const shownEffective = top && resolved ? plan.addable.filter((f) => resolved[f.name] !== undefined && resolved[f.name].source !== 'written') : [];
    const shownNames = new Set(shownEffective.map((f) => f.name));
    // Effective values that are no words of the schema (a room's surfaces from its theme): read only.
    const extra = top && resolved ? Object.entries(resolved).filter(([name, entry]) => !(name in value) && entry.source !== 'written' && !plan.addable.some((f) => f.name === name)
        && !plan.groups.some((g) => g.fields.some((f) => f.name === name))) : [];
    return (
        <div className={css.object}>
            {plan.discriminator ? (
                <div className={css.note}>
                    {plan.discriminator.property}: <b>{String(plan.discriminator.value)}</b>
                    {plan.hiddenByKind > 0 ? ` · ${plan.hiddenByKind} words of other kinds hidden` : ''}
                </div>
            ) : null}
            {plan.variant ? <div className={css.note}>form: <b>{plan.variant.labels[plan.variant.active]}</b></div> : null}
            {plan.groups.map((g) => (
                g.name ? (
                    <section key={g.name} className={css.section}>
                        <h4 className={css.sectionTitle}>{g.name}</h4>
                        {g.fields.map(fieldOf)}
                    </section>
                ) : <div key="_" className={css.section}>{g.fields.map(fieldOf)}</div>
            ))}
            {plan.unknown.map((k) => (
                <div key={k} className={css.row} data-missing>
                    <span className={css.label}>{k}</span>
                    <code className={css.raw}>{JSON.stringify(value[k])}</code>
                    <span className={css.tools}>{edits ? <RemoveButton path={[...path, k]} /> : null}</span>
                </div>
            ))}
            {shownEffective.length > 0 || extra.length > 0 ? (
                <section className={css.section} data-testid="not-written">
                    <h4 className={css.sectionTitle}>Not written (the values that apply)</h4>
                    {shownEffective.map(fieldOf)}
                    {extra.map(([name, entry]) => (
                        <div key={name} className={`${css.row} ${css.notWritten}`}>
                            <span className={css.label} title={name}>{humanise(name)}</span>
                            <span className={css.control}><span className={css.effective}>{effectiveText(entry)}</span></span>
                            <span className={css.tools}><span className={css.from}>{entry.from ?? entry.source}</span></span>
                        </div>
                    ))}
                </section>
            ) : null}
            {edits ? <AddField fields={plan.addable.filter((f) => !shownNames.has(f.name))} path={path} />
                : plan.addable.length > 0 ? <div className={css.dim}>{plan.addable.length} more words not written (Author mode adds them)</div> : null}
        </div>
    );
}
