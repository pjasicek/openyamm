// Inputs that commit on Enter or on leaving the field (S5_BROWSER_EDITOR.md 2.7: "a field being typed in lives in
// the browser until Enter or leaving it"), shared by the inspector and the tool options. Esc puts the value back.
import { useEffect, useRef, useState } from 'react';
import { evaluate } from './plan.ts';
import css from './Fields.module.css';

interface CommitProps<T>
{
    value: T | undefined;
    onCommit: (value: T) => void;
    placeholder?: string;
    disabled?: boolean;
    // The value shown greyed when none is written (the effective value from the core: "not written").
    effective?: string;
    title?: string;
    testId?: string;
    width?: 'narrow' | 'wide';
}

export function NumberInput({ value, onCommit, placeholder, disabled, effective, title, testId, width, integer, min, max }: CommitProps<number> & { integer?: boolean; min?: number; max?: number })
{
    const shown = value === undefined ? '' : String(value);
    const [text, setText] = useState(shown);
    const [bad, setBad] = useState(false);
    // Enter commits and leaves the field, and leaving it commits: the text committed once is not sent again before
    // the new value comes back.
    const sent = useRef<string | null>(null);
    useEffect(() =>
    {
        setText(shown);
        setBad(false);
        sent.current = null;
    }, [shown]);
    const commit = () =>
    {
        if (text.trim() === '' || text === shown)
        {
            setText(shown);
            return;
        }
        if (text === sent.current)
        {
            return;
        }
        // Expressions are welcome: 512*3, (1024 - 64) / 2.
        let number = evaluate(text);
        if (number === undefined)
        {
            setBad(true);
            return;
        }
        if (integer)
        {
            number = Math.round(number);
        }
        setBad((min !== undefined && number < min) || (max !== undefined && number > max));
        setText(String(number));
        if (number !== value)
        {
            sent.current = text;
            onCommit(number);
        }
    };
    return (
        <input
            className={`${css.input} ${width === 'narrow' ? css.narrow : ''}`}
            data-bad={bad || undefined}
            data-effective={value === undefined && effective !== undefined ? '' : undefined}
            value={text}
            placeholder={value === undefined && effective !== undefined ? `${effective} (not written)` : placeholder}
            disabled={disabled}
            title={title ?? (min !== undefined || max !== undefined ? `${min ?? '…'} to ${max ?? '…'}; expressions such as 512*3 are worked out` : 'expressions such as 512*3 are worked out')}
            inputMode="decimal"
            data-testid={testId}
            onChange={(event) => setText(event.target.value)}
            onFocus={() => { sent.current = null; }}
            onBlur={commit}
            onKeyDown={(event) =>
            {
                if (event.key === 'Enter')
                {
                    commit();
                    (event.target as HTMLInputElement).blur();
                }
                else if (event.key === 'Escape')
                {
                    setText(shown);
                    (event.target as HTMLInputElement).blur();
                }
            }}
        />
    );
}

export function TextInput({ value, onCommit, placeholder, disabled, effective, title, testId, width, pattern }: CommitProps<string> & { pattern?: string })
{
    const shown = value ?? '';
    const [text, setText] = useState(shown);
    const [bad, setBad] = useState(false);
    const sent = useRef<string | null>(null);
    useEffect(() =>
    {
        setText(shown);
        setBad(false);
        sent.current = null;
    }, [shown]);
    const commit = () =>
    {
        if (text === shown || text === sent.current)
        {
            return;
        }
        if (pattern && !new RegExp(pattern).test(text))
        {
            setBad(true);
            return;
        }
        setBad(false);
        sent.current = text;
        onCommit(text);
    };
    return (
        <input
            className={`${css.input} ${width === 'wide' ? css.wide : ''}`}
            data-bad={bad || undefined}
            value={text}
            placeholder={value === undefined && effective !== undefined ? `${effective} (not written)` : placeholder}
            disabled={disabled}
            title={title ?? (pattern ? `the form: ${pattern}` : undefined)}
            data-testid={testId}
            onChange={(event) => setText(event.target.value)}
            onFocus={() => { sent.current = null; }}
            onBlur={commit}
            onKeyDown={(event) =>
            {
                if (event.key === 'Enter')
                {
                    commit();
                    (event.target as HTMLInputElement).blur();
                }
                else if (event.key === 'Escape')
                {
                    setText(shown);
                    (event.target as HTMLInputElement).blur();
                }
            }}
        />
    );
}
