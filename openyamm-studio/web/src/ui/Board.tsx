// The switch board (S5_BROWSER_EDITOR.md 3.7): the events that move things (and the switches no event uses yet) down
// the side, the doors, lifts, movers and levers across, what each event does to each in the cells. A view of
// wiring.yml, not a data type: a click on a cell is one patch of one event (none, toggles, opens, closes, none), or a
// new event for a switch without one.
import { useMemo } from 'react';
import { boardOf, cellChange, verbOf } from '../edit/wiring.ts';
import type { BoardRow } from '../edit/wiring.ts';
import { useActions, useS } from './context.ts';
import css from './Board.module.css';
import { VariablesPanel } from './Variables.tsx';

const MARK: Record<string, string> = { toggles: 'T', opens: 'O', closes: 'C' };

export function SwitchBoard()
{
    const actions = useActions();
    const files = useS((s) => (s.project.state === 'ready' ? s.project.value.files : undefined));
    const author = useS((s) => s.mode === 'author');
    const selection = useS((s) => s.selection?.id ?? null);
    const board = useMemo(() => boardOf(files), [files]);
    const click = (row: BoardRow, target: string) =>
    {
        if (!author)
        {
            actions.notify('Switch to Author mode to change the wiring');
            return;
        }
        const change = cellChange(files, row, target);
        if (change)
        {
            void actions.edit({ label: change.label, ops: change.ops });
        }
    };
    if (board.rows.length === 0 && board.columns.length === 0)
    {
        return (
            <div className={css.board} data-testid="board">
                <VariablesPanel />
                <div className={css.empty}>No switches, doors or events yet: make a switch (Build, W) and a door (Build, D), then link them here or with L.</div>
            </div>
        );
    }
    return (
        <div className={css.board} data-testid="board">
            <VariablesPanel />
            <p className={css.legend}>
                <b>Switch board</b> · a cell: <span className={css.mark}>T</span> toggles, <span className={css.mark}>O</span> opens, <span className={css.mark}>C</span> closes;
                a click cycles it (none, T, O, C) as one change of that event. A row's name selects its event; a column's its object.
            </p>
            <div className={css.scroll}>
                <table className={css.table}>
                    <thead>
                        <tr>
                            <th className={css.corner}>event (source) \ moves</th>
                            {board.columns.map((column) => (
                                <th key={column} className={`${css.column} ${selection === column ? css.selected : ''}`}>
                                    <button type="button" className={css.link} onClick={() => actions.select({ id: column, file: 'objects.yml' }, true)}>{column}</button>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {board.rows.map((row, index) =>
                        {
                            const id = row.event ? String(row.event.id) : row.source!;
                            return (
                                <tr key={`${id}-${index}`} className={selection === id || (row.source && selection === row.source) ? css.selected : ''}>
                                    <th className={css.row}>
                                        <button type="button" className={css.link} data-testid={`board-row-${id}`}
                                            onClick={() => actions.select({ id, file: row.event ? 'wiring.yml' : 'objects.yml' }, true)}>{row.label}</button>
                                    </th>
                                    {board.columns.map((column) =>
                                    {
                                        const verb = row.event ? verbOf(row.event, column) : null;
                                        const self = row.source === column;
                                        return (
                                            <td key={column} className={css.cell}>
                                                <button type="button" className={verb ? css.on : css.off} disabled={self || !author} data-testid={`cell-${id}-${column}`}
                                                    title={self ? 'its own source' : `${id} ${verb ?? 'does not move'} ${column}: click for ${verb === null ? 'toggles' : verb === 'toggles' ? 'opens' : verb === 'opens' ? 'closes' : 'none'}`}
                                                    onClick={() => click(row, column)}>{self ? '·' : verb ? MARK[verb] : ''}</button>
                                            </td>
                                        );
                                    })}
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
