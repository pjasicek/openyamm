// Walk mode in the 3D view (S5_BROWSER_EDITOR.md 3.6): the party of the game's size walks the built map with the
// game's own movement code, in the WebAssembly worker (walk.worker.ts). Mouse look with the browser's pointer lock
// (a click on the view takes it; Esc gives it back, and a second Esc leaves walk mode), WASD or the arrows, Shift
// runs, Space jumps; a click while looking toggles the door, lift or mover in the middle of the view. Each animation
// frame sends the keys and the frame's length to the worker (walk.step) and puts the camera at the eye it answers.
import type { WalkLoadResult, WalkPose } from '../../../schema/rpc/generated/rpc.ts';
import type { Camera } from '../model/pins.ts';
import type { WalkFiles, WalkReply, WalkRequest } from './protocol.ts';
import type { WalkChannel, WalkChannelReply, WalkChannelRequest } from '../rpc/client.ts';
import { buttonsOf, cameraOfWalk, isWalkKey, look } from './input.ts';

// What walk mode needs of the 3D view (viewport/Viewport.ts).
export interface WalkView
{
    canvasElement(): HTMLCanvasElement;
    camera(): Camera;
    setWalkCamera(camera: Camera): void;
    setWalking(on: boolean): void;
    pickCentre(): { owner: string; base: string } | null;
    setHiddenObjects(ids: ReadonlySet<string>): void;
}

export interface WalkCallbacks
{
    onPose(pose: WalkPose): void;
    onLocked(locked: boolean): void;
    onDoor(id: string, open: boolean): void;
    onNote(text: string): void;
    // Leaving walk mode (the second Esc).
    onLeave(): void;
}

export interface WalkTimings
{
    coreMs: number;
    fetchMs: number;
    loadMs: number;
    bytes: number;
    // Each walk.step: the round trip from the page and the call inside the worker, milliseconds.
    steps: number[];
    calls: number[];
}

// Walk mode's own worker (local mode): the core loaded from the host, the walk's files fetched with the token.
class WalkWorker implements WalkChannel
{
    private readonly worker: Worker;
    private nextId = 1;
    private readonly waiting = new Map<number, (reply: WalkReply) => void>();

    constructor()
    {
        this.worker = new Worker(new URL('./walk.worker.ts', import.meta.url), { type: 'module' });
        this.worker.onmessage = (event: MessageEvent<WalkReply>) =>
        {
            const done = this.waiting.get(event.data.id);
            this.waiting.delete(event.data.id);
            done?.(event.data);
        };
    }

    send(request: WalkChannelRequest): Promise<WalkChannelReply>
    {
        return this.post(request as Unnumbered<WalkRequest>);
    }

    private post(request: Unnumbered<WalkRequest>): Promise<WalkReply>
    {
        const id = this.nextId++;
        return new Promise((resolve) =>
        {
            this.waiting.set(id, resolve);
            this.worker.postMessage({ ...request, id } as WalkRequest);
        });
    }

    terminate(): void
    {
        this.worker.terminate();
    }
}

const DOOR_KINDS = ['door:', 'lift:', 'mover:', 'switch:'];

// A request without its id (the worker client numbers them), for each kind of request.
type Unnumbered<T> = T extends unknown ? Omit<T, 'id'> : never;

export class WalkMode
{
    private readonly view: WalkView;
    private readonly callbacks: WalkCallbacks;
    private readonly worker: WalkChannel;
    private readonly keys = new Set<string>();
    private yaw = 0;
    private pitch = 0;
    private running = false;
    private inFlight = false;
    private owed = 0;
    private last = 0;
    private locked = false;
    private unlockedAt = 0;
    private readonly openDoors = new Set<string>();
    load: WalkLoadResult | null = null;
    pose: WalkPose | null = null;
    readonly timings: WalkTimings = { coreMs: 0, fetchMs: 0, loadMs: 0, bytes: 0, steps: [], calls: [] };
    // Keys pressed since the last step, so a tap shorter than a frame (a jump) still reaches the walk.
    private readonly tapped = new Set<string>();

    // `channel`: the worker that runs the walk (hosted mode: the page's one worker); none: walk mode's own.
    constructor(view: WalkView, callbacks: WalkCallbacks, channel: WalkChannel | null = null)
    {
        this.view = view;
        this.callbacks = callbacks;
        this.worker = channel ?? new WalkWorker();
    }

    private async call<T>(method: string, params: unknown): Promise<T>
    {
        const reply = await this.worker.send({ type: 'call', method, params });
        if (reply.answer.error)
        {
            throw new Error(reply.answer.error.message);
        }
        return reply.answer.result as T;
    }

    // Loads the walk and puts the party where the camera's eye is.
    async start(files: WalkFiles, token: string, coreUrl?: string): Promise<WalkLoadResult>
    {
        const reply = await this.worker.send({ type: 'load', files, token, ...(coreUrl ? { coreUrl } : {}) });
        if (reply.answer.error)
        {
            throw new Error(reply.answer.error.message);
        }
        Object.assign(this.timings, reply.timing ?? {});
        this.load = reply.answer.result as WalkLoadResult;
        for (const door of this.load.doors)
        {
            if (door.open)
            {
                this.openDoors.add(door.id);
            }
        }
        const camera = this.view.camera();
        this.yaw = camera.yaw;
        this.pitch = Math.max(-1.2, Math.min(1.2, camera.pitch));
        const placed = await this.call<{ pose: WalkPose }>('walk.place', { eye: camera.eye });
        this.setPose(placed.pose);
        this.view.setWalking(true);
        this.attach();
        this.running = true;
        this.last = performance.now();
        requestAnimationFrame(this.tick);
        return this.load;
    }

    // Puts the party at a camera's eye (the game's exit pose), keeping walk mode on.
    async placeAt(camera: Camera): Promise<void>
    {
        this.yaw = camera.yaw;
        this.pitch = camera.pitch;
        const placed = await this.call<{ pose: WalkPose }>('walk.place', { eye: camera.eye });
        this.setPose(placed.pose);
    }

    stop(): void
    {
        this.running = false;
        this.detach();
        if (document.pointerLockElement === this.view.canvasElement())
        {
            document.exitPointerLock();
        }
        this.view.setWalking(false);
        this.view.setHiddenObjects(new Set());
        this.worker.terminate();
    }

    // The keys held and the view's facing (scripted runs set them without a keyboard or a mouse).
    hold(code: string, down: boolean): void
    {
        if (down)
        {
            this.keys.add(code);
            this.tapped.add(code);
        }
        else
        {
            this.keys.delete(code);
        }
    }

    face(yaw: number, pitch: number): void
    {
        this.yaw = yaw;
        this.pitch = pitch;
        if (this.pose)
        {
            this.view.setWalkCamera(cameraOfWalk(this.pose, this.yaw, this.pitch));
        }
    }

    async toggle(id: string): Promise<boolean>
    {
        const answer = await this.call<{ door: string; open: boolean }>('walk.toggle', { door: id });
        if (answer.open)
        {
            this.openDoors.add(id);
        }
        else
        {
            this.openDoors.delete(id);
        }
        // An open door is drawn away (the view's mesh is the map as built, doors shut).
        this.view.setHiddenObjects(new Set(this.openDoors));
        this.callbacks.onDoor(id, answer.open);
        return answer.open;
    }

    private setPose(pose: WalkPose): void
    {
        this.pose = pose;
        this.view.setWalkCamera(cameraOfWalk(pose, this.yaw, this.pitch));
        this.callbacks.onPose(pose);
    }

    private readonly tick = (now: number) =>
    {
        if (!this.running)
        {
            return;
        }
        this.owed = Math.min(0.1, this.owed + Math.max(0, (now - this.last) / 1000));
        this.last = now;
        if (!this.inFlight && this.owed > 0)
        {
            const seconds = this.owed;
            this.owed = 0;
            this.inFlight = true;
            const started = performance.now();
            const buttons = buttonsOf([...this.keys, ...this.tapped]);
            this.tapped.clear();
            void this.worker.send({ type: 'call', method: 'walk.step', params: { yaw_radians: this.yaw, buttons, seconds } })
                .then((reply) =>
                {
                    this.inFlight = false;
                    if (reply.answer.error)
                    {
                        this.callbacks.onNote(`Walk step failed: ${reply.answer.error.message}`);
                        return;
                    }
                    if (this.timings.steps.length < 4000)
                    {
                        this.timings.steps.push(performance.now() - started);
                        this.timings.calls.push(reply.timing?.callMs ?? 0);
                    }
                    if (this.running)
                    {
                        this.setPose((reply.answer.result as { pose: WalkPose }).pose);
                    }
                });
        }
        requestAnimationFrame(this.tick);
    };

    // --- input ------------------------------------------------------------------------------------------------------

    private attach(): void
    {
        window.addEventListener('keydown', this.onKeyDown, true);
        window.addEventListener('keyup', this.onKeyUp, true);
        window.addEventListener('blur', this.onBlur);
        document.addEventListener('pointerlockchange', this.onLockChange);
        document.addEventListener('mousemove', this.onMouseMove);
        this.view.canvasElement().addEventListener('mousedown', this.onMouseDown);
    }

    private detach(): void
    {
        window.removeEventListener('keydown', this.onKeyDown, true);
        window.removeEventListener('keyup', this.onKeyUp, true);
        window.removeEventListener('blur', this.onBlur);
        document.removeEventListener('pointerlockchange', this.onLockChange);
        document.removeEventListener('mousemove', this.onMouseMove);
        this.view.canvasElement().removeEventListener('mousedown', this.onMouseDown);
    }

    private readonly onKeyDown = (event: KeyboardEvent) =>
    {
        const target = event.target as HTMLElement | null;
        if (target?.closest('input, textarea, .cm-editor'))
        {
            return;
        }
        if (event.code === 'Escape')
        {
            // The Esc that gave back the pointer is the browser's; one more leaves walk mode.
            event.stopPropagation();
            if (!this.locked && performance.now() - this.unlockedAt > 250)
            {
                this.callbacks.onLeave();
            }
            return;
        }
        if (isWalkKey(event.code) && !event.ctrlKey && !event.metaKey && !event.altKey)
        {
            this.keys.add(event.code);
            this.tapped.add(event.code);
            event.preventDefault();
            event.stopPropagation();
        }
    };

    private readonly onKeyUp = (event: KeyboardEvent) =>
    {
        this.keys.delete(event.code);
    };

    private readonly onBlur = () => this.keys.clear();

    private readonly onLockChange = () =>
    {
        this.locked = document.pointerLockElement === this.view.canvasElement();
        if (!this.locked)
        {
            this.unlockedAt = performance.now();
            this.keys.clear();
        }
        this.callbacks.onLocked(this.locked);
    };

    private readonly onMouseMove = (event: MouseEvent) =>
    {
        if (!this.locked)
        {
            return;
        }
        const next = look(this.yaw, this.pitch, event.movementX, event.movementY);
        this.face(next.yaw, next.pitch);
    };

    private readonly onMouseDown = (event: MouseEvent) =>
    {
        event.stopPropagation();
        if (!this.locked)
        {
            void this.view.canvasElement().requestPointerLock();
            return;
        }
        const pick = this.view.pickCentre();
        const id = pick?.base ?? '';
        if (DOOR_KINDS.some((kind) => id.startsWith(kind)))
        {
            this.toggle(id).catch((error) => this.callbacks.onNote(error instanceof Error ? error.message : String(error)));
        }
    };
}
