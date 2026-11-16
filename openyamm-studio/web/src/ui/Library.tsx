// The drawer's Library (S5_BROWSER_EDITOR.md 3.10): the asset catalogue (`assets.search`): the world's face
// textures with their sizes and decorations with theirs. Drag a texture onto a wall, floor or ceiling in the plan or
// the 3D view (on the plan: near a wall for that wall, else the floor; Shift: the ceiling; Alt: the room's walls), or
// lay it from here on the selected room or on a theme; drag a decoration onto the plan or 3D to place it, or take it
// as the Decoration tool's.
import { useEffect, useMemo, useState } from 'react';
import { Menu } from '@base-ui/react/menu';
import type { AssetsSearchResult } from '../../../schema/rpc/generated/rpc.ts';
import { ASSET_MIME } from '../edit/drop.ts';
import type { LibraryAsset, LibraryKind } from '../edit/drop.ts';
import type { SurfacePart } from '../edit/surfaces.ts';
import { themeOfRoom } from '../edit/surfaces.ts';
import { roomById } from '../edit/ops.ts';
import { useActions, useS, useStudioContext } from './context.ts';
import css from './Library.module.css';

type Kind = LibraryKind;

const KINDS: { kind: Kind; label: string; first: string }[] = [
    { kind: 'texture', label: 'Textures', first: 't1w' }, { kind: 'decoration', label: 'Decorations', first: 'torch' },
    { kind: 'monster', label: 'Monsters', first: 'goblin' }, { kind: 'item', label: 'Items', first: 'potion' }, { kind: 'sound', label: 'Sounds', first: 'drip' },
];

function sizeText(entry: { size?: number[]; width?: number; height?: number; liquid?: string }): string
{
    if (entry.liquid)
    {
        return `liquid (${entry.liquid})`;
    }
    const size = entry.size?.length === 2 ? entry.size : entry.width && entry.height ? [entry.width, entry.height] : null;
    return size ? `${size[0]} × ${size[1]}` : '';
}

export function LibraryPanel()
{
    const actions = useActions();
    const { store } = useStudioContext();
    const [kind, setKind] = useState<Kind>('texture');
    const [query, setQuery] = useState('t1w');
    const [answer, setAnswer] = useState<AssetsSearchResult | string | null>(null);
    const [busy, setBusy] = useState(false);
    const selection = useS((s) => s.selection?.id ?? null);
    const files = useS((s) => (s.project.state === 'ready' ? s.project.value.files : undefined));
    const author = useS((s) => s.mode === 'author');
    useEffect(() =>
    {
        const words = query.trim();
        if (words.length < 1)
        {
            setAnswer(null);
            return;
        }
        let live = true;
        setBusy(true);
        const timer = setTimeout(() =>
        {
            void actions.searchAssets(words, kind).then((result) =>
            {
                if (live)
                {
                    setAnswer(result);
                    setBusy(false);
                }
            });
        }, 250);
        return () =>
        {
            live = false;
            clearTimeout(timer);
        };
    }, [actions, query, kind]);
    // The room the selection is in (a room, or a block of one) and the theme it is drawn with.
    const room = selection?.startsWith('room:') ? selection.split('/')[0] : null;
    const theme = useMemo(() =>
    {
        const object = room && files ? roomById(files, room) : undefined;
        return object && files ? themeOfRoom(files, object) : null;
    }, [room, files]);
    const rows: LibraryAsset[] = typeof answer === 'object' && answer
        ? kind === 'texture'
            ? (answer.textures ?? []).map((entry) => ({ kind: 'texture' as const, name: entry.name, ...(entry.size ? { size: entry.size } : {}),
                ...(entry.width ? { width: entry.width } : {}), ...(entry.height ? { height: entry.height } : {}) }))
            : kind === 'monster' ? (answer.monsters ?? []).map((entry) => ({ kind: 'monster' as const, name: entry.name, number: entry.number }))
            : kind === 'item' ? (answer.items ?? []).map((entry) => ({ kind: 'item' as const, name: entry.name, number: entry.number }))
            : kind === 'sound' ? (answer.sounds ?? []).map((entry) => ({ kind: 'sound' as const, name: entry.name }))
            : (answer.decorations ?? []).map((entry) => ({ kind: 'decoration' as const, name: entry.name }))
        : [];
    const detail = (name: string, number?: number): string =>
    {
        if (typeof answer !== 'object' || !answer)
        {
            return '';
        }
        if (kind === 'texture')
        {
            const entry = answer.textures?.find((texture) => texture.name === name);
            return entry ? [sizeText(entry), entry.note ?? '', entry.usable_on_faces ? '' : 'name too long for a face'].filter(Boolean).join(' · ') : '';
        }
        if (kind === 'monster')
        {
            const monster = answer.monsters?.find((entry) => entry.number === number);
            return monster ? `#${monster.number} · ${monster.picture} · level ${monster.level}, ${monster.hp} hit points` : '';
        }
        if (kind === 'item')
        {
            const item = answer.items?.find((entry) => entry.number === number);
            return item ? `#${item.number} · ${item.kind} · ${item.value} gold` : '';
        }
        if (kind === 'sound')
        {
            return answer.sounds?.find((entry) => entry.name === name)?.file ?? '';
        }
        const entry = answer.decorations?.find((decoration) => decoration.name === name);
        return entry ? `${entry.hint} · radius ${entry.radius}, ${entry.height} high${entry.light_radius ? ` · light ${entry.light_radius}` : ''} · ${entry.indoor_model}` : '';
    };
    const apply = (asset: LibraryAsset, target: { room: string } | { theme: string }, part: SurfacePart) => actions.applySurface(asset, target, part);
    return (
        <div className={css.library} data-testid="library">
            <div className={css.bar}>
                <span className={css.kinds} role="group" aria-label="Kind">
                    {KINDS.map((entry) => (
                        <button key={entry.kind} type="button" className={entry.kind === kind ? css.kindOn : css.kind} data-testid={`library-${entry.kind}`}
                            onClick={() => { setKind(entry.kind); setQuery(entry.first); }}>{entry.label}</button>
                    ))}
                </span>
                <input className={css.search} value={query} onChange={(event) => setQuery(event.target.value)} placeholder="words of the name (t1w, crypt, torch)"
                    data-testid="library-search" aria-label="Search the library" />
                <span className={css.dim}>{busy ? 'searching…' : typeof answer === 'string' ? answer : answer ? `${answer.matches} found${answer.matches > rows.length ? `, ${rows.length} shown` : ''}` : ''}</span>
            </div>
            <p className={css.help}>
                {kind === 'texture'
                    ? 'Drag a texture onto the plan (near a wall: that wall; inside: the floor; Shift: the ceiling; Alt: the walls) or onto a face in 3D, or use “lay on”.'
                    : kind === 'decoration' ? 'Drag a decoration onto the plan or 3D (near a wall it hangs there), or click to take it as the Decoration tool\'s.'
                    : `Drag ${kind === 'sound' ? 'a sound' : kind === 'monster' ? 'a monster' : 'an item'} onto the plan or 3D to place it there, or click to take it as the ${kind === 'sound' ? 'Sound' : kind === 'monster' ? 'Monster' : 'Item'} tool's.`}
            </p>
            <div className={css.list}>
                {rows.map((asset) => (
                    <div key={asset.number !== undefined ? `${asset.kind}-${asset.number}` : asset.name} className={css.row} draggable={author}
                        data-testid={asset.number !== undefined ? `asset-${asset.kind}-${asset.number}` : `asset-${asset.name}`}
                        onDragStart={(event) =>
                        {
                            event.dataTransfer.setData(ASSET_MIME, JSON.stringify(asset));
                            event.dataTransfer.setData('text/plain', asset.name);
                            event.dataTransfer.effectAllowed = 'copy';
                        }}
                        onClick={() =>
                        {
                            if (asset.kind === 'decoration')
                            {
                                store.setState((s) => ({ toolOptions: { ...s.toolOptions, decoration: asset.name } }));
                                actions.setTool('decoration');
                            }
                            else if (asset.kind === 'monster' || asset.kind === 'item' || asset.kind === 'sound')
                            {
                                const value = asset.kind === 'sound' ? asset.name : String(asset.number ?? asset.name);
                                store.setState((s) => ({ toolOptions: { ...s.toolOptions, [asset.kind]: value } }));
                                actions.setTool(asset.kind);
                            }
                        }}>
                        <span className={css.name}>{asset.name}</span>
                        <span className={css.detail}>{detail(asset.name, asset.number)}</span>
                        {asset.kind === 'texture' && author ? (
                            <Menu.Root>
                                <Menu.Trigger className={css.lay} data-testid={`lay-${asset.name}`} onClick={(event) => event.stopPropagation()}>lay on ▾</Menu.Trigger>
                                <Menu.Portal>
                                    <Menu.Positioner className={css.positioner} sideOffset={4} align="end">
                                        <Menu.Popup className={css.menu}>
                                            {room ? (['wall', 'floor', 'ceiling'] as const).map((part) => (
                                                <Menu.Item key={`room-${part}`} className={css.item} onClick={() => apply(asset, { room }, part)} data-testid={`lay-room-${part}`}>
                                                    {part === 'wall' ? 'the walls' : `the ${part}`} of {room}
                                                </Menu.Item>
                                            )) : <div className={css.itemDim}>Select a room to lay it on that room</div>}
                                            {theme ? (['wall', 'floor', 'ceiling'] as const).map((part) => (
                                                <Menu.Item key={`theme-${part}`} className={css.item} onClick={() => apply(asset, { theme }, part)} data-testid={`lay-theme-${part}`}>
                                                    {part === 'wall' ? 'the walls' : `the ${part}`} of every room of {theme}
                                                </Menu.Item>
                                            )) : null}
                                        </Menu.Popup>
                                    </Menu.Positioner>
                                </Menu.Portal>
                            </Menu.Root>
                        ) : null}
                    </div>
                ))}
                {rows.length === 0 && typeof answer === 'object' && answer ? <div className={css.empty}>Nothing of that name.</div> : null}
            </div>
        </div>
    );
}
