// The hosted page's project actions in the title bar (S5c; S5_BROWSER_EDITOR.md 1.3 F3 steps 4 to 6): build in the
// page's core, export the project's source, the build or the mod folder as a zip, or write the mod folder into a folder
// the person picks (the install's mods/, File System Access). Where the project is saved is said beside them.
import { useState } from 'react';
import { Popover } from '@base-ui/react/popover';
import { useS, useStudioContext } from '../ui/context.ts';
import type { HostedClient } from './client.ts';
import css from './Hosted.module.css';

function download(bytes: Uint8Array, name: string): void
{
    const url = URL.createObjectURL(new Blob([bytes as unknown as BlobPart], { type: 'application/zip' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = name;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
}

export function HostedMenu()
{
    const { controller } = useStudioContext();
    const client = controller?.client;
    const key = useS((s) => s.projectKey);
    const projects = useS((s) => s.projects);
    const [note, setNote] = useState<string>('');
    const [busy, setBusy] = useState(false);
    if (!client || client.mode !== 'hosted' || !key)
    {
        return null;
    }
    const hosted = client as HostedClient;
    const saved = projects.state === 'ready' ? projects.value.find((project) => project.key === key)?.label ?? '' : '';
    const act = async (what: string, work: () => Promise<string>) =>
    {
        setBusy(true);
        setNote(`${what}…`);
        try
        {
            setNote(await work());
        }
        catch (error)
        {
            setNote(`${what}: ${error instanceof Error ? error.message : String(error)}`);
        }
        finally
        {
            setBusy(false);
        }
    };
    const canPickFolder = typeof (window as unknown as { showDirectoryPicker?: unknown }).showDirectoryPicker === 'function';
    return (
        <span className={css.menu} data-testid="hosted-menu">
            <button type="button" className={css.menuButton} disabled={busy} data-testid="hosted-build"
                onClick={() => void act('Building', async () =>
                {
                    const started = performance.now();
                    const built = await hosted.call('build.run', { project: key, dry_run: false });
                    return `Built ${built.map} (${built.files.length} files) in ${Math.round(performance.now() - started)} ms`;
                })} title="Builds the map in this page (the same bytes as the studio on your computer)">Build</button>
            <Popover.Root>
                <Popover.Trigger className={css.menuButton} data-testid="hosted-files" title={saved ? `Saved to ${saved}` : 'Export or install'}>Files ▾</Popover.Trigger>
                <Popover.Portal>
                    <Popover.Positioner sideOffset={6} align="end" className={css.positioner}>
                        <Popover.Popup className={css.popup} data-testid="hosted-files-popup">
                            <p className={css.dim}>{saved ? `Saved to ${saved}.` : ''}</p>
                            <button type="button" className={css.menuItem} disabled={busy} data-testid="hosted-export-build"
                                onClick={() => void act('Exporting the build', async () =>
                                {
                                    const zip = await hosted.exportZip(key, 'build');
                                    download(zip.bytes, `${key}-build.zip`);
                                    return `The build: ${zip.files} files`;
                                })}>Export the build (zip)<span>the map, its scene and script, as built</span></button>
                            <button type="button" className={css.menuItem} disabled={busy} data-testid="hosted-export-mod"
                                onClick={() => void act('Exporting the mod folder', async () =>
                                {
                                    const zip = await hosted.exportZip(key, 'mod');
                                    download(zip.bytes, `${key}-mod.zip`);
                                    return `The mod folder: ${zip.files} files (unpack into the game's mods folder)`;
                                })}>Export as a mod (zip)<span>laid out as the game's mods folder: unpack it into &lt;install&gt;/mods</span></button>
                            {canPickFolder ? (
                                <button type="button" className={css.menuItem} disabled={busy} data-testid="hosted-save-mod"
                                    onClick={() => void act('Writing the mod folder', async () =>
                                    {
                                        const picker = (window as unknown as { showDirectoryPicker: (options: object) => Promise<FileSystemDirectoryHandle> }).showDirectoryPicker;
                                        const handle = await picker({ mode: 'readwrite' });
                                        const written = await hosted.saveTo(key, 'mod', handle);
                                        return `Wrote ${written.files} files into ${handle.name}`;
                                    })}>Install into the game's mods folder…<span>choose &lt;install&gt;/mods: the game plays it at its next start</span></button>
                            ) : null}
                            <button type="button" className={css.menuItem} disabled={busy} data-testid="hosted-export-project"
                                onClick={() => void act('Exporting the project', async () =>
                                {
                                    const zip = await hosted.exportZip(key, 'project');
                                    download(zip.bytes, `${key}.zip`);
                                    return `The project's source: ${zip.files} files`;
                                })}>Export the project (zip)<span>its files, for other modders (without the build and the history)</span></button>
                            <p className={css.dim}>Play here and playtests need the game: pair with the studio on your computer, or install the mod and start the game.</p>
                        </Popover.Popup>
                    </Popover.Positioner>
                </Popover.Portal>
            </Popover.Root>
            <span className={css.menuNote} title={note} data-testid="hosted-note">{note}</span>
        </span>
    );
}
