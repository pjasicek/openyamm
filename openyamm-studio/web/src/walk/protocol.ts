// The messages between the page and walk mode's worker (walk.worker.ts).
export interface WalkFiles
{
    map: string;
    state: string;
    decorations: string;
    terrain?: string;
}

export type WalkRequest =
    | { id: number; type: 'load'; files: WalkFiles; token: string; coreUrl?: string }
    | { id: number; type: 'call'; method: string; params: unknown };

export interface WalkReply
{
    id: number;
    answer: { result?: unknown; error?: { message: string; data?: { kind?: string } } };
    timing?: { coreMs?: number; fetchMs?: number; loadMs?: number; bytes?: number; callMs?: number };
}
