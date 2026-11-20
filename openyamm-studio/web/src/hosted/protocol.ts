// The messages between the hosted page and its worker (hosted.worker.ts; S5_BROWSER_EDITOR.md 2.2 "Hosted mode").
// The worker holds the WebAssembly core, the asset root and the open projects; the page sends requests and gets
// answers, and the worker sends the notices a local host would send.
import type { OpenedProject } from './session.ts';

// What the person picked: a folder by its File System Access handle (Chromium), or files with their paths inside
// what was picked (a folder through <input webkitdirectory>, single zips, or a drop).
export type Picked =
    | { kind: 'handle'; handle: FileSystemDirectoryHandle; writable: boolean }
    | { kind: 'files'; files: { path: string; file: File }[] };

// Where a project is kept besides the core's memory.
export type ProjectPlace =
    | { kind: 'folder'; handle: FileSystemDirectoryHandle }
    | { kind: 'browser'; name: string }
    | { kind: 'memory' };

export interface InstallSummary
{
    kind: 'install' | 'packages' | 'tree';
    release: string | null;
    packages: number;
    entries: number;
    worlds: string[];
    bytes: number;
    ms: number;
}

export interface WorkerStats
{
    heap: { live: number; arena: number; memory: number; peak: number };
    reads: { reads: number; bytesRead: number; inflated: number; inflatedBytes: number; cacheBytes: number };
    textures: { textures: number; bytes: number };
    timings: { method: string; ms: number }[];
}

export type HostedRequest =
    | { id: number; type: 'init'; coreUrl: string; version: string }
    | { id: number; type: 'open_assets'; picked: Picked }
    | { id: number; type: 'open_project'; picked: Picked | { kind: 'zip'; file: File } | { kind: 'browser'; name: string }; place: 'folder' | 'browser' | 'memory'; name: string }
    | { id: number; type: 'new_project'; place: ProjectPlace; params: Record<string, unknown> }
    | { id: number; type: 'import_map'; place: ProjectPlace; map: string; world: string }
    | { id: number; type: 'browser_projects' }
    | { id: number; type: 'call'; method: string; params: Record<string, unknown> }
    | { id: number; type: 'bytes'; path: string }
    | { id: number; type: 'walk_load'; files: { map: string; state: string; decorations: string; terrain?: string } }
    | { id: number; type: 'export'; key: string; what: 'project' | 'build' | 'mod' }
    | { id: number; type: 'save_to'; key: string; what: 'build' | 'mod'; handle: FileSystemDirectoryHandle }
    | { id: number; type: 'close'; key: string }
    | { id: number; type: 'stats'; timings?: boolean };

export type HostedReply =
    | { id: number; ok: true; value: unknown; timing?: Record<string, number> }
    | { id: number; ok: false; message: string };

export type HostedNotice = { type: 'notice'; method: string; params: Record<string, unknown> };

export type { OpenedProject };
