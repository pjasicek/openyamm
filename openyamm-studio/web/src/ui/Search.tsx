// Search (S5_BROWSER_EDITOR.md 3.16): objects by id, on Base UI's combo box. Bound to Ctrl P: Ctrl K belongs to the
// browser in Chrome (the user's key check, 2026-11-14 17:32), so 3.17's fallback is the binding.
import { useEffect, useMemo, useRef, useState } from 'react';
import { Combobox } from '@base-ui/react/combobox';
import { searchIds } from '../model/objects.ts';
import { NONE } from '../state/store.ts';
import { useActions, useS } from './context.ts';
import css from './Search.module.css';

export function Search()
{
    const ids = useS((s) => (s.project.state === 'ready' ? s.project.value.ids : NONE));
    const actions = useActions();
    const [query, setQuery] = useState('');
    const input = useRef<HTMLInputElement>(null);
    const hits = useMemo(() => searchIds(ids, query, 40).map((place) => `${place.id}\u0000${place.file}`), [ids, query]);

    useEffect(() =>
    {
        const onKey = (event: KeyboardEvent) =>
        {
            if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'p')
            {
                event.preventDefault();
                input.current?.focus();
                input.current?.select();
            }
        };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, []);

    return (
        <Combobox.Root
            items={hits}
            filter={null}
            inputValue={query}
            onInputValueChange={(value) => setQuery(value)}
            value={null}
            onValueChange={(chosen) =>
            {
                const value = chosen as unknown;
                if (typeof value === 'string')
                {
                    const [id, file] = value.split('\u0000');
                    actions.select({ id, file }, true);
                    setQuery('');
                    input.current?.blur();
                }
            }}
        >
            <Combobox.Input ref={input} className={css.input} placeholder="Search objects (Ctrl P)" aria-label="Search objects" />
            <Combobox.Portal>
                <Combobox.Positioner className={css.positioner} sideOffset={4} align="start">
                    <Combobox.Popup className={css.popup}>
                        <Combobox.Empty className={css.empty}>{query ? 'No object has that in its id' : 'Type part of an id'}</Combobox.Empty>
                        <Combobox.List>
                            {(item: string) =>
                            {
                                const [id, file] = item.split('\u0000');
                                return (
                                    <Combobox.Item key={item} value={item} className={css.item}>
                                        <span className={css.id}>{id}</span>
                                        <span className={css.file}>{file}</span>
                                    </Combobox.Item>
                                );
                            }}
                        </Combobox.List>
                    </Combobox.Popup>
                </Combobox.Positioner>
            </Combobox.Portal>
        </Combobox.Root>
    );
}
