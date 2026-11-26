// The 3D view's one owner of three.js (S5_BROWSER_EDITOR.md 4.4, "Containment"): nothing else in the app imports
// three. The rest talks to it in the studio's terms: load the core's mesh, set a texture, highlight objects, pick,
// frame. three.js is pinned at 0.186.1, WebGL2. Map axes are kept as they are (x east, y north, z up): the camera's
// up is +z, so no coordinate is converted. It handles WebGL context loss by keeping what it uploaded (the mesh's
// buffers and the textures' blocks stay in memory) and re-uploading all of it when the context comes back.
import * as THREE from 'three';
import type { Pin, ViewMeshResult } from '../../../schema/rpc/generated/rpc.ts';
import type { Camera } from '../model/pins.ts';
import { pinPlace, statusOf } from '../model/pins.ts';
import type { ParsedTexture } from './oytex.ts';
import { Codec } from './oytex.ts';
import { gameFrameIn, studioVerticalFov } from './gameCamera.ts';
import type { Travel } from './travel.ts';
import { poseTriangles } from './travel.ts';
import { HALF, NODES } from '../edit/cells.ts';

export interface PickResult
{
    // The face's owner as the provenance table names it (room:hall/walls/3), its top-level id, and its file.
    owner: string;
    base: string;
    file?: string;
    face: number;
    point: [number, number, number];
    // The face's normal (a dropped texture tells a floor from a ceiling by it).
    normal?: [number, number, number];
}

export interface ViewportCallbacks
{
    onHover(pick: PickResult | null): void;
    onPick(pick: PickResult | null): void;
    onCamera?(position: [number, number, number]): void;
}

export interface ViewportCapabilities
{
    bc7: boolean;
    bc1: boolean;
    rgtc: boolean;
    renderer: string;
}

interface GroupEntry
{
    texture: string;
    kind: string;
    uvUnit: string;
    material: THREE.Material;
}

const TERRAIN_CHUNK_CELLS = 16;
export class Viewport
{
    private readonly root: HTMLElement;
    private readonly callbacks: ViewportCallbacks;
    private readonly renderer: THREE.WebGLRenderer;
    private readonly scene = new THREE.Scene();
    private readonly camera_ = new THREE.PerspectiveCamera(60, 1, 8, 400000);
    private readonly raycaster = new THREE.Raycaster();
    private readonly world = new THREE.Group();
    private readonly overlays = new THREE.Group();
    private readonly cutPlane = new THREE.Plane(new THREE.Vector3(0, 0, -1), 0);
    private readonly textures = new Map<string, { texture: THREE.CompressedTexture; parsed: ParsedTexture }>();
    private readonly resizeObserver: ResizeObserver;
    private meta: ViewMeshResult | null = null;
    private geometry: THREE.BufferGeometry | null = null;
    private mainMesh: THREE.Mesh | null = null;
    private terrainChunks: { mesh: THREE.Mesh; triangles: Uint32Array }[] = [];
    private groups: GroupEntry[] = [];
    private triangleFaces: Uint32Array = new Uint32Array(0);
    private faceOwners: Uint32Array = new Uint32Array(0);
    private ownerBase: Int32Array = new Int32Array(0);
    private baseIds: string[] = [];
    private indices: Uint32Array = new Uint32Array(0);
    private selectionOverlay: THREE.Mesh | null = null;
    private hoverOverlay: THREE.Mesh | null = null;
    private selectionId: string | null = null;
    private hoverId: string | null = null;
    // Walk mode (walk/WalkMode.ts): the camera is the party's eye, the orbit and fly controls are off, and the open
    // doors are drawn away (their faces out of the mesh, a faint ghost left to click them shut again).
    private walking = false;
    // The outline of the game's frame over the view (walk mode), and whether it is shown.
    private readonly frameOutline: HTMLDivElement;
    private frameShown = false;
    private hiddenIds = new Set<string>();
    private originalIndices: Uint32Array | null = null;
    private ghost: { mesh: THREE.Mesh; triangles: Uint32Array } | null = null;
    private textured = true;
    private cutaway = false;
    private dirty = true;
    private running = true;
    private contextLost = false;
    private liquids: THREE.MeshLambertMaterial[] = [];
    private readonly pinMarkers = new THREE.Group();
    // History's "show as it was": the rooms of an earlier state as lines over the current.
    private readonly historyGhost = new THREE.Group();
    private pins: Pin[] = [];
    private selectedPin: string | null = null;
    // The last face under the pointer (a pin made with P is made on it).
    lastHover: PickResult | null = null;
    // Camera: orbit about `target` (yaw, pitch, distance); right mouse looks and WASD flies.
    private readonly target = new THREE.Vector3();
    private yaw = -Math.PI / 2;
    private pitch = -0.9;
    private distance = 4000;
    private drag: { x: number; y: number; button: number; shift: boolean; moved: boolean; yaw: number; pitch: number; target: THREE.Vector3 } | null = null;
    private readonly keys = new Set<string>();
    private lastTick = performance.now();
    private hoverQueued: { x: number; y: number } | null = null;
    readonly capabilities: ViewportCapabilities;
    contextRestores = 0;
    framesDrawn = 0;
    lastFrameMs = 0;

    constructor(root: HTMLElement, callbacks: ViewportCallbacks)
    {
        this.root = root;
        this.callbacks = callbacks;
        this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance', preserveDrawingBuffer: false });
        this.renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
        this.renderer.outputColorSpace = THREE.SRGBColorSpace;
        this.renderer.localClippingEnabled = false;
        this.renderer.domElement.className = 'oy-viewport-canvas';
        this.renderer.domElement.tabIndex = 0;
        root.append(this.renderer.domElement);
        this.frameOutline = document.createElement('div');
        this.frameOutline.className = 'oy-game-frame';
        this.frameOutline.hidden = true;
        root.append(this.frameOutline);
        const gl = this.renderer.getContext();
        const debug = gl.getExtension('WEBGL_debug_renderer_info');
        this.capabilities = {
            bc7: !!gl.getExtension('EXT_texture_compression_bptc'),
            bc1: !!gl.getExtension('WEBGL_compressed_texture_s3tc'),
            rgtc: !!gl.getExtension('EXT_texture_compression_rgtc'),
            renderer: String(debug ? gl.getParameter(debug.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER)),
        };
        gl.getExtension('WEBGL_compressed_texture_s3tc_srgb');
        this.camera_.up.set(0, 0, 1);
        this.scene.add(this.world, this.overlays, this.pinMarkers, this.historyGhost);
        // Simple light (3.5: grey, textured and simple-lit; the game's look is Play here's job): enough from every
        // side that walls seen from above are not black.
        this.scene.add(new THREE.AmbientLight(0xffffff, 1.3));
        this.scene.add(new THREE.HemisphereLight(0xffffff, 0x8a877e, 1.2));
        const sun = new THREE.DirectionalLight(0xffffff, 0.7);
        sun.position.set(0.35, 0.6, 1);
        this.scene.add(sun);
        this.applyTokens();

        const canvas = this.renderer.domElement;
        canvas.addEventListener('webglcontextlost', this.onContextLost);
        canvas.addEventListener('webglcontextrestored', this.onContextRestored);
        canvas.addEventListener('pointerdown', this.onPointerDown);
        canvas.addEventListener('pointermove', this.onPointerMove);
        canvas.addEventListener('pointerup', this.onPointerUp);
        canvas.addEventListener('pointerleave', () => this.setHover(null, true));
        canvas.addEventListener('wheel', this.onWheel, { passive: false });
        canvas.addEventListener('contextmenu', (event) => event.preventDefault());
        canvas.addEventListener('keydown', this.onKeyDown);
        canvas.addEventListener('keyup', this.onKeyUp);
        canvas.addEventListener('blur', () => this.keys.clear());
        this.resizeObserver = new ResizeObserver(() => this.resize());
        this.resizeObserver.observe(root);
        this.resize();
        this.updateCamera();
        requestAnimationFrame(this.tick);
    }

    dispose(): void
    {
        this.running = false;
        this.resizeObserver.disconnect();
        this.clearMesh();
        for (const entry of this.textures.values())
        {
            entry.texture.dispose();
        }
        this.textures.clear();
        this.renderer.dispose();
        this.renderer.domElement.remove();
        this.frameOutline.remove();
    }

    // Colours from the design tokens (the background, grey, liquids, highlights).
    applyTokens(): void
    {
        const style = getComputedStyle(document.documentElement);
        const token = (name: string, fallback: string) => style.getPropertyValue(`--${name}`).trim() || fallback;
        this.scene.background = new THREE.Color(token('view-bg', '#30343a'));
        this.tokenColours = {
            grey: new THREE.Color(token('view-grey', '#b8b4ac')),
            liquid: new THREE.Color(token('view-liquid', '#3a6fa0')),
            select: new THREE.Color(token('view-select', '#4a90e2')),
            hover: new THREE.Color(token('view-hover', '#f0a030')),
        };
        this.pinColours = {
            open: new THREE.Color(token('plan-pin', '#d1450d')),
            claimed: new THREE.Color(token('warn', '#a35b00')),
            resolved: new THREE.Color(token('good', '#2e7d32')),
            accepted: new THREE.Color(token('text-dim', '#6a655c')),
            declined: new THREE.Color(token('text-dim', '#6a655c')),
        };
        this.refreshPins();
        this.dirty = true;
    }

    // The rooms of an earlier state (view.layout_at) as lines: each outline at its floor and ceiling and the corners
    // between, seen through the walls; null puts them away.
    setGhost(rooms: readonly { outline: readonly (readonly number[])[]; floor: number; ceiling: number }[] | null): void
    {
        for (const child of [...this.historyGhost.children])
        {
            const line = child as THREE.LineSegments;
            line.geometry.dispose();
            (line.material as THREE.Material).dispose();
            this.historyGhost.remove(child);
        }
        if (rooms && rooms.length > 0)
        {
            const positions: number[] = [];
            for (const room of rooms)
            {
                const n = room.outline.length;
                for (let i = 0; i < n; ++i)
                {
                    const a = room.outline[i];
                    const b = room.outline[(i + 1) % n];
                    for (const z of [room.floor, room.ceiling])
                    {
                        positions.push(a[0], a[1], z, b[0], b[1], z);
                    }
                    positions.push(a[0], a[1], room.floor, a[0], a[1], room.ceiling);
                }
            }
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
            const lines = new THREE.LineSegments(geometry, new THREE.LineBasicMaterial({ color: 0xe0a020, depthTest: false, transparent: true, opacity: 0.85 }));
            lines.renderOrder = 10;
            this.historyGhost.add(lines);
        }
        this.dirty = true;
    }

    private pinColours: Record<string, THREE.Color> = {};

    // The pins as markers standing over their places (their point, or where they were made from), coloured by
    // status, seen through walls; the selected one larger.
    setPins(pins: Pin[], selected: string | null): void
    {
        this.pins = pins;
        this.selectedPin = selected;
        this.refreshPins();
    }

    private refreshPins(): void
    {
        for (const marker of [...this.pinMarkers.children])
        {
            marker.traverse((child) =>
            {
                const mesh = child as THREE.Mesh;
                mesh.geometry?.dispose();
                (mesh.material as THREE.Material | undefined)?.dispose();
            });
            this.pinMarkers.remove(marker);
        }
        for (const pin of this.pins)
        {
            const place = pinPlace(pin);
            if (!place)
            {
                continue;
            }
            const status = statusOf(pin);
            const closed = status === 'accepted' || status === 'declined';
            const colour = this.pinColours[status] ?? new THREE.Color(0xd1450d);
            const material = (paint: THREE.Color, side: THREE.Side = THREE.FrontSide) => new THREE.MeshBasicMaterial({
                color: paint, depthTest: false, transparent: true, opacity: closed ? 0.45 : 1, side,
            });
            // A map pin standing on its place: a head over a point, outlined, drawn over the walls; sized on screen
            // as the camera moves (render()).
            const marker = new THREE.Group();
            const head = new THREE.Mesh(new THREE.SphereGeometry(10, 16, 12), material(colour));
            head.position.z = 30;
            const rim = new THREE.Mesh(new THREE.SphereGeometry(12.5, 16, 12), material(new THREE.Color(0xffffff), THREE.BackSide));
            rim.position.z = 30;
            const point = new THREE.Mesh(new THREE.ConeGeometry(6, 22, 12), material(colour));
            point.rotation.x = -Math.PI / 2;
            point.position.z = 11;
            head.renderOrder = 12;
            point.renderOrder = 12;
            rim.renderOrder = 11;
            marker.add(rim, point, head);
            marker.position.set(place[0], place[1], place[2] + (pin.at ? 0 : 120));
            marker.name = pin.id;
            marker.userData.selected = pin.id === this.selectedPin;
            this.pinMarkers.add(marker);
        }
        this.dirty = true;
    }

    // Pins keep about the same size on screen at any distance (about 28 pixels tall, 40 when selected).
    private scalePins(): void
    {
        const perPixel = (2 * Math.tan((this.camera_.fov * Math.PI) / 360)) / Math.max(1, this.renderer.domElement.clientHeight);
        for (const marker of this.pinMarkers.children)
        {
            const distance = marker.position.distanceTo(this.camera_.position);
            const pixels = marker.userData.selected ? 40 : 28;
            marker.scale.setScalar(Math.max(0.2, (distance * perPixel * pixels) / 42));
        }
    }

    // The camera put where a pin was made from (S5_BROWSER_EDITOR.md 3.13 "go to"): at the eye, facing as the
    // party faced; orbiting then turns about a point a little ahead.
    setCamera(camera: Camera): void
    {
        const distance = 192;
        this.yaw = camera.yaw;
        this.pitch = Math.max(-1.55, Math.min(1.55, camera.pitch));
        this.distance = distance;
        this.target.set(camera.eye[0], camera.eye[1], camera.eye[2]).addScaledVector(this.direction(), distance);
        this.updateCamera();
    }

    camera(): Camera
    {
        return { eye: [this.camera_.position.x, this.camera_.position.y, this.camera_.position.z], yaw: this.yaw, pitch: this.pitch };
    }

    // The camera at an eye, turning about the eye itself (walk mode: the party's eye each frame).
    setWalkCamera(camera: Camera): void
    {
        this.yaw = camera.yaw;
        this.pitch = Math.max(-1.55, Math.min(1.55, camera.pitch));
        this.distance = 1;
        this.target.set(camera.eye[0], camera.eye[1], camera.eye[2]).addScaledVector(this.direction(), this.distance);
        this.updateCamera();
    }

    setWalking(on: boolean): void
    {
        this.walking = on;
        this.setFrameShown(on);
        this.keys.clear();
        this.drag = null;
        if (!on && this.distance < 64)
        {
            // Back to orbiting: about a point a little ahead of the eye.
            const eye = this.camera_.position.clone();
            this.distance = 192;
            this.target.copy(eye).addScaledVector(this.direction(), this.distance);
            this.updateCamera();
        }
    }

    canvasElement(): HTMLCanvasElement
    {
        return this.renderer.domElement;
    }

    // Objects drawn away (their top-level ids): walk mode's open doors.
    setHiddenObjects(ids: ReadonlySet<string>): void
    {
        this.hiddenIds = new Set(ids);
        this.applyHidden();
    }

    private applyHidden(): void
    {
        if (!this.geometry || !this.mainMesh)
        {
            return;
        }
        if (this.ghost)
        {
            this.overlays.remove(this.ghost.mesh);
            this.ghost.mesh.geometry.dispose();
            (this.ghost.mesh.material as THREE.Material).dispose();
            this.ghost = null;
        }
        this.originalIndices ??= this.indices.slice();
        const hidden = new Set([...this.hiddenIds, ...this.travelHidden].map((id) => this.baseIds.indexOf(id)).filter((index) => index >= 0));
        const indices = this.originalIndices.slice();
        const ghostIndices: number[] = [];
        const ghostTriangles: number[] = [];
        if (hidden.size > 0)
        {
            for (let t = 0; t < this.triangleFaces.length; ++t)
            {
                if (hidden.has(this.ownerBase[this.triangleFaces[t]]))
                {
                    ghostIndices.push(indices[t * 3], indices[t * 3 + 1], indices[t * 3 + 2]);
                    ghostTriangles.push(t);
                    // A degenerate triangle keeps the groups' ranges as they are.
                    indices[t * 3 + 1] = indices[t * 3];
                    indices[t * 3 + 2] = indices[t * 3];
                }
            }
        }
        this.geometry.setIndex(new THREE.BufferAttribute(indices, 1));
        if (ghostIndices.length > 0)
        {
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', this.geometry.getAttribute('position'));
            geometry.setIndex(new THREE.BufferAttribute(Uint32Array.from(ghostIndices), 1));
            geometry.computeBoundingSphere();
            const material = new THREE.MeshBasicMaterial({ color: this.tokenColours.hover, transparent: true, opacity: 0.12,
                depthWrite: false, side: THREE.DoubleSide });
            const mesh = new THREE.Mesh(geometry, material);
            mesh.matrixAutoUpdate = false;
            this.overlays.add(mesh);
            this.ghost = { mesh, triangles: Uint32Array.from(ghostTriangles) };
        }
        this.dirty = true;
    }

    // The view as a JPEG data URL at most `maxWidth` wide (a pin's picture): drawn now and read at once, so the
    // drawing buffer need not be kept.
    capture(maxWidth = 1280, quality = 0.85): string
    {
        this.render();
        const source = this.renderer.domElement;
        if (source.width <= maxWidth)
        {
            return source.toDataURL('image/jpeg', quality);
        }
        const scaled = document.createElement('canvas');
        scaled.width = maxWidth;
        scaled.height = Math.round((source.height * maxWidth) / source.width);
        scaled.getContext('2d')!.drawImage(source, 0, 0, scaled.width, scaled.height);
        return scaled.toDataURL('image/jpeg', quality);
    }

    // The face at the middle of the view.
    pickCentre(): PickResult | null
    {
        const rect = this.renderer.domElement.getBoundingClientRect();
        return this.pickAt(rect.width / 2, rect.height / 2);
    }

    private tokenColours = {
        grey: new THREE.Color(0xb8b4ac),
        liquid: new THREE.Color(0x3a6fa0),
        select: new THREE.Color(0x4a90e2),
        hover: new THREE.Color(0xf0a030),
    };

    // The last good triangles (positions, three points each) of objects a view build left out (2.4.2), by top-level
    // id: drawn hatched in place of the object until a build includes it again.
    private staleTriangles = new Map<string, Float32Array>();
    private staleMesh: THREE.Object3D | null = null;

    // An object's triangles in the mesh shown now, as plain positions.
    private trianglesOf(base: string): Float32Array | null
    {
        const index = this.baseIds.indexOf(base);
        const geometry = this.geometry;
        if (index < 0 || !geometry || !this.originalIndicesOrIndex())
        {
            return null;
        }
        const positions = geometry.getAttribute('position').array as Float32Array;
        const indices = this.originalIndicesOrIndex()!;
        const out: number[] = [];
        for (let t = 0; t < this.triangleFaces.length; ++t)
        {
            if (this.ownerBase[this.triangleFaces[t]] === index)
            {
                for (let k = 0; k < 3; ++k)
                {
                    const v = indices[t * 3 + k];
                    out.push(positions[v * 3], positions[v * 3 + 1], positions[v * 3 + 2]);
                }
            }
        }
        return out.length > 0 ? Float32Array.from(out) : null;
    }

    private originalIndicesOrIndex(): Uint32Array | null
    {
        return this.originalIndices ?? this.indices ?? null;
    }

    // Keeps the last good mesh of each object the new view build left out, from the mesh shown now or the stale set.
    private keepStale(skipped: readonly string[]): void
    {
        const kept = new Map<string, Float32Array>();
        for (const id of skipped)
        {
            const base = id.split('/')[0];
            const triangles = this.trianglesOf(base) ?? this.staleTriangles.get(base);
            if (triangles)
            {
                kept.set(base, triangles);
            }
        }
        this.staleTriangles = kept;
    }

    private drawStale(): void
    {
        if (this.staleMesh)
        {
            this.world.remove(this.staleMesh);
            this.staleMesh.traverse((object) =>
            {
                if (object instanceof THREE.Mesh || object instanceof THREE.LineSegments)
                {
                    object.geometry.dispose();
                    (object.material as THREE.Material).dispose();
                }
            });
            this.staleMesh = null;
        }
        if (this.staleTriangles.size === 0)
        {
            return;
        }
        const all = new Float32Array([...this.staleTriangles.values()].reduce((sum, part) => sum + part.length, 0));
        let at = 0;
        for (const part of this.staleTriangles.values())
        {
            all.set(part, at);
            at += part.length;
        }
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(all, 3));
        geometry.computeBoundingSphere();
        const group = new THREE.Group();
        // Stale: translucent in the warning colour, its edges drawn, so it reads as "not built now".
        const warn = new THREE.Color(getComputedStyle(document.documentElement).getPropertyValue('--warn').trim() || '#a35b00');
        group.add(new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({ color: warn, transparent: true, opacity: 0.22, depthWrite: false, side: THREE.DoubleSide })));
        group.add(new THREE.LineSegments(new THREE.WireframeGeometry(geometry), new THREE.LineBasicMaterial({ color: warn, transparent: true, opacity: 0.7 })));
        group.matrixAutoUpdate = false;
        this.staleMesh = group;
        this.world.add(group);
    }

    // The core's mesh (view.mesh) and its bytes. Textures already set are kept (by name). Objects the view build
    // left out (meta.skipped) keep their last good triangles, drawn stale.
    loadMesh(meta: ViewMeshResult, bytes: ArrayBuffer, frame: boolean): void
    {
        this.keepStale(meta.skipped ?? []);
        this.clearMesh();
        this.meta = meta;
        const section = (name: keyof ViewMeshResult['sections'], Type: Float32ArrayConstructor | Uint32ArrayConstructor) =>
        {
            const s = meta.sections[name];
            return new Type(bytes, s.offset, s.count);
        };
        const positions = section('positions', Float32Array) as Float32Array;
        const normals = section('normals', Float32Array) as Float32Array;
        const uvs = section('uvs', Float32Array) as Float32Array;
        this.indices = section('indices', Uint32Array) as Uint32Array;
        this.triangleFaces = section('triangle_faces', Uint32Array) as Uint32Array;
        this.faceOwners = section('face_owners', Uint32Array) as Uint32Array;
        this.baseIds = [];
        const baseOf = new Map<string, number>();
        const ownerBaseByOwner = meta.owners.map((owner) =>
        {
            if (!owner.id)
            {
                return -1;
            }
            const base = owner.id.split('/')[0];
            let index = baseOf.get(base);
            if (index === undefined)
            {
                index = this.baseIds.length;
                this.baseIds.push(base);
                baseOf.set(base, index);
            }
            return index;
        });
        this.ownerBase = new Int32Array(this.faceOwners.length);
        this.faceOwners.forEach((owner, face) => { this.ownerBase[face] = ownerBaseByOwner[owner] ?? -1; });

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('normal', new THREE.BufferAttribute(normals, 3));
        geometry.setAttribute('uv', new THREE.BufferAttribute(uvs, 2));
        geometry.setIndex(new THREE.BufferAttribute(this.indices, 1));
        geometry.computeBoundingBox();
        geometry.computeBoundingSphere();
        this.geometry = geometry;

        const materials: THREE.Material[] = [];
        this.groups = meta.groups.map((group, index) =>
        {
            const material = this.makeMaterial(group.texture, group.kind);
            materials.push(material);
            if (group.kind !== 'terrain')
            {
                geometry.addGroup(group.first, group.count, index);
            }
            return { texture: group.texture, kind: group.kind, uvUnit: group.uv_unit, material };
        });
        const mesh = new THREE.Mesh(geometry, materials);
        mesh.matrixAutoUpdate = false;
        this.mainMesh = mesh;
        this.world.add(mesh);
        this.makeTerrainChunks(positions);
        for (const name of this.textures.keys())
        {
            this.bindTexture(name);
        }
        if (frame && !this.walking)
        {
            this.frameBounds(meta.bounds.min, meta.bounds.max);
        }
        this.refreshOverlays();
        // The scrubbed object of the old mesh: posed again on the new one (S5b2).
        const scrub = this.travelShown;
        this.dropTravelMesh();
        if (this.hiddenIds.size > 0)
        {
            this.applyHidden();
        }
        if (scrub)
        {
            this.setTravel(scrub.travel, scrub.t);
        }
        this.drawStale();
        this.dirty = true;
    }

    // A texture's levels (the low ones first, then the whole chain): replaces what the name had.
    setTexture(name: string, parsed: ParsedTexture): void
    {
        const supported = (parsed.header.codec === Codec.Bc7 && this.capabilities.bc7)
            || (parsed.header.codec === Codec.Bc1 && this.capabilities.bc1)
            || ((parsed.header.codec === Codec.Bc4 || parsed.header.codec === Codec.Bc5) && this.capabilities.rgtc);
        if (!supported)
        {
            return;
        }
        const format = parsed.header.codec === Codec.Bc7 ? THREE.RGBA_BPTC_Format
            : parsed.header.codec === Codec.Bc1 ? THREE.RGBA_S3TC_DXT1_Format
            : parsed.header.codec === Codec.Bc4 ? THREE.RED_RGTC1_Format : THREE.RED_GREEN_RGTC2_Format;
        const mips = parsed.mips.map((mip) => ({ data: mip.data, width: mip.width, height: mip.height }));
        const texture = new THREE.CompressedTexture(mips as unknown as ImageData[], mips[0].width, mips[0].height, format);
        texture.wrapS = THREE.RepeatWrapping;
        texture.wrapT = THREE.RepeatWrapping;
        texture.magFilter = THREE.LinearFilter;
        texture.minFilter = mips.length > 1 ? THREE.LinearMipmapLinearFilter : THREE.LinearFilter;
        texture.anisotropy = 4;
        texture.generateMipmaps = false;
        texture.colorSpace = parsed.header.codec === Codec.Bc7 || parsed.header.codec === Codec.Bc1 ? THREE.SRGBColorSpace : THREE.NoColorSpace;
        texture.needsUpdate = true;
        const old = this.textures.get(name);
        this.textures.set(name, { texture, parsed });
        this.bindTexture(name);
        old?.texture.dispose();
        this.dirty = true;
    }

    textureNames(): string[]
    {
        const names = new Set<string>();
        for (const group of this.meta?.groups ?? [])
        {
            if (group.texture)
            {
                names.add(group.texture);
            }
        }
        return [...names];
    }

    setTextured(on: boolean): void
    {
        this.textured = on;
        for (const name of this.textures.keys())
        {
            this.bindTexture(name);
        }
        for (const group of this.groups)
        {
            if (!this.textures.has(group.texture) && group.kind !== 'liquid' && group.material instanceof THREE.MeshLambertMaterial)
            {
                group.material.color.copy(this.tokenColours.grey);
            }
        }
        this.dirty = true;
    }

    setCutaway(on: boolean): void
    {
        this.cutaway = on;
        this.renderer.clippingPlanes = on ? [this.cutPlane] : [];
        this.dirty = true;
    }

    setSelection(id: string | null): void
    {
        if (id !== this.selectionId)
        {
            this.selectionId = id;
            this.refreshOverlays();
        }
    }

    setHoverId(id: string | null): void
    {
        if (id !== this.hoverId)
        {
            this.hoverId = id;
            this.refreshOverlays();
        }
    }

    // Frames the faces of one object (its top-level id), or the whole mesh.
    frameObject(id: string | null): void
    {
        if (!this.geometry || !this.meta)
        {
            return;
        }
        if (!id)
        {
            this.frameBounds(this.meta.bounds.min, this.meta.bounds.max);
            return;
        }
        const base = this.baseIds.indexOf(id);
        if (base < 0)
        {
            return;
        }
        const box = new THREE.Box3();
        const position = this.geometry.getAttribute('position') as THREE.BufferAttribute;
        const point = new THREE.Vector3();
        for (let t = 0; t < this.triangleFaces.length; ++t)
        {
            if (this.ownerBase[this.triangleFaces[t]] === base)
            {
                for (let k = 0; k < 3; ++k)
                {
                    box.expandByPoint(point.fromBufferAttribute(position, this.indices[t * 3 + k]));
                }
            }
        }
        if (!box.isEmpty())
        {
            // Some room round one object: its surroundings show where it is.
            const size = box.getSize(new THREE.Vector3());
            box.expandByVector(new THREE.Vector3(Math.max(512, size.x * 0.6), Math.max(512, size.y * 0.6), 0));
            this.frameBounds(box.min.toArray(), box.max.toArray());
        }
    }

    framePoint(at: readonly number[], radius = 768): void
    {
        this.frameBounds([at[0] - radius, at[1] - radius, at[2] - radius], [at[0] + radius, at[1] + radius, at[2] + radius]);
    }

    frameBounds(min: readonly number[], max: readonly number[]): void
    {
        const centre = new THREE.Vector3((min[0] + max[0]) / 2, (min[1] + max[1]) / 2, (min[2] + max[2]) / 2);
        // Looking north and down, as the plan shows the map (north up, east right): the box's plan fills the view.
        const halfHeight = Math.tan((this.camera_.fov * Math.PI) / 360);
        const halfWidth = halfHeight * this.camera_.aspect;
        const spanX = Math.max(512, max[0] - min[0]);
        const spanY = Math.max(512, max[1] - min[1], max[2] - min[2]);
        this.target.copy(centre);
        this.distance = Math.max(spanX / (2 * halfWidth), (spanY * 0.75) / (2 * halfHeight)) * 1.05;
        this.yaw = Math.PI / 2;
        this.pitch = -0.95;
        this.updateCamera();
    }

    // Picks at a point of the canvas (CSS pixels): the face and its owner.
    // A page point's pick (a drop from the Library), or null outside the view.
    pickClient(clientX: number, clientY: number): PickResult | null
    {
        const rect = this.renderer.domElement.getBoundingClientRect();
        if (clientX < rect.left || clientY < rect.top || clientX > rect.right || clientY > rect.bottom)
        {
            return null;
        }
        return this.pickAt(clientX - rect.left, clientY - rect.top);
    }

    // The page point of a world point (scripted runs click in the view by it), or null behind the camera.
    clientOf(x: number, y: number, z: number): [number, number] | null
    {
        this.camera_.updateMatrixWorld();
        const point = new THREE.Vector3(x, y, z).project(this.camera_);
        if (point.z > 1)
        {
            return null;
        }
        const rect = this.renderer.domElement.getBoundingClientRect();
        return [rect.left + (point.x + 1) / 2 * rect.width, rect.top + (1 - point.y) / 2 * rect.height];
    }

    pickAt(x: number, y: number): PickResult | null
    {
        if (!this.mainMesh || !this.meta)
        {
            return null;
        }
        const rect = this.renderer.domElement.getBoundingClientRect();
        const ndc = new THREE.Vector2((x / rect.width) * 2 - 1, -(y / rect.height) * 2 + 1);
        this.raycaster.setFromCamera(ndc, this.camera_);
        const targets: THREE.Object3D[] = [this.mainMesh, ...this.terrainChunks.map((chunk) => chunk.mesh),
            ...(this.ghost ? [this.ghost.mesh] : [])];
        const hits = this.raycaster.intersectObjects(targets, false);
        for (const hit of hits)
        {
            if (this.cutaway && hit.point.z > this.cutPlane.constant)
            {
                continue;
            }
            let triangle = hit.faceIndex ?? -1;
            const chunk = this.terrainChunks.find((candidate) => candidate.mesh === hit.object);
            if (chunk && triangle >= 0)
            {
                triangle = chunk.triangles[triangle];
            }
            if (this.ghost && hit.object === this.ghost.mesh && triangle >= 0)
            {
                triangle = this.ghost.triangles[triangle];
            }
            if (triangle < 0 || triangle >= this.triangleFaces.length)
            {
                continue;
            }
            const face = this.triangleFaces[triangle];
            const ownerIndex = this.faceOwners[face] ?? 0;
            const owner = this.meta.owners[ownerIndex] ?? { id: '' };
            return {
                owner: owner.id,
                base: owner.id.split('/')[0],
                file: owner.file,
                face,
                point: [Math.round(hit.point.x), Math.round(hit.point.y), Math.round(hit.point.z)],
                ...(hit.face ? { normal: [hit.face.normal.x, hit.face.normal.y, hit.face.normal.z] as [number, number, number] } : {}),
            };
        }
        return null;
    }

    // Timing of `count` picks at random points (the hover budget of 2.13): the milliseconds of each.
    measurePicks(count: number): number[]
    {
        const rect = this.renderer.domElement.getBoundingClientRect();
        const times: number[] = [];
        let seed = 12345;
        const random = () => ((seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff);
        for (let i = 0; i < count; ++i)
        {
            const start = performance.now();
            this.pickAt(random() * rect.width, random() * rect.height);
            times.push(performance.now() - start);
        }
        return times;
    }

    // Frames a second drawn back to back, each finished on the GPU (an upper bound on frame time).
    measureFrameRate(frames: number): { fps: number; meanMs: number }
    {
        const gl = this.renderer.getContext();
        const pixel = new Uint8Array(4);
        const start = performance.now();
        for (let i = 0; i < frames; ++i)
        {
            this.yaw += 0.01;
            this.updateCamera();
            this.renderer.render(this.scene, this.camera_);
            gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, pixel);
        }
        const ms = performance.now() - start;
        return { fps: (frames * 1000) / ms, meanMs: ms / frames };
    }

    // Draws now and waits for the GPU (the screenshot run's marks).
    renderNow(): void
    {
        this.render();
        const gl = this.renderer.getContext();
        gl.finish();
    }

    // For tests of context loss: loses and restores the WebGL context.
    simulateContextLoss(): boolean
    {
        const extension = this.renderer.getContext().getExtension('WEBGL_lose_context');
        if (!extension)
        {
            return false;
        }
        extension.loseContext();
        setTimeout(() => extension.restoreContext(), 50);
        return true;
    }

    cameraPosition(): [number, number, number]
    {
        return [this.camera_.position.x, this.camera_.position.y, this.camera_.position.z];
    }

    // --- internals ----------------------------------------------------------------------------------------------

    private makeMaterial(texture: string, kind: string): THREE.Material
    {
        if (kind === 'liquid')
        {
            // The game draws these as liquids, but some (shore tiles matched by a prefix) have a picture: the
            // texture is asked for all the same, and the animated colour stays only where none comes.
            const material = new THREE.MeshLambertMaterial({ color: this.tokenColours.liquid.clone(), name: texture });
            this.liquids.push(material);
            return material;
        }
        return new THREE.MeshLambertMaterial({ color: this.tokenColours.grey.clone(), side: THREE.FrontSide, name: texture });
    }

    private bindTexture(name: string): void
    {
        const entry = this.textures.get(name);
        if (!entry)
        {
            return;
        }
        for (const group of this.groups)
        {
            if (group.texture !== name || !(group.material instanceof THREE.MeshLambertMaterial))
            {
                continue;
            }
            const material = group.material;
            if (this.textured)
            {
                // Texels to the texture's own size, as the game divides them (its logical size: width / scale).
                const map = entry.texture;
                if (group.uvUnit === 'texel')
                {
                    const header = entry.parsed.header;
                    map.repeat.set(entry.parsed.scale / header.width, entry.parsed.scale / header.height);
                }
                material.map = map;
                material.color.setRGB(1, 1, 1);
                material.alphaTest = entry.parsed.header.alphaUse !== 0 ? 0.5 : 0;
            }
            else
            {
                material.map = null;
                material.color.copy(this.tokenColours.grey);
                material.alphaTest = 0;
            }
            material.needsUpdate = true;
        }
    }

    // The land's triangles in chunks of 16 x 16 cells, each its own mesh with its own bounds, so a pick tests only
    // the chunks its ray passes (no picking tree; S5_BROWSER_EDITOR.md 2.13).
    private makeTerrainChunks(positions: Float32Array): void
    {
        if (!this.meta || !this.geometry)
        {
            return;
        }
        const chunkSize = TERRAIN_CHUNK_CELLS * 512;
        for (const [index, group] of this.meta.groups.entries())
        {
            if (group.kind !== 'terrain')
            {
                continue;
            }
            const byChunk = new Map<number, number[]>();
            for (let t = group.first / 3; t < (group.first + group.count) / 3; ++t)
            {
                const a = this.indices[t * 3];
                // From the map's south-west corner and one map further out (positive whatever the side).
                const cx = Math.floor((positions[a * 3] + 2 * HALF) / chunkSize);
                const cy = Math.floor((positions[a * 3 + 1] + 2 * HALF) / chunkSize);
                const key = cy * 1024 + cx;
                let list = byChunk.get(key);
                if (!list)
                {
                    list = [];
                    byChunk.set(key, list);
                }
                list.push(t);
            }
            for (const triangles of byChunk.values())
            {
                const index3 = new Uint32Array(triangles.length * 3);
                triangles.forEach((t, i) => index3.set(this.indices.subarray(t * 3, t * 3 + 3), i * 3));
                const geometry = new THREE.BufferGeometry();
                geometry.setAttribute('position', this.geometry.getAttribute('position'));
                geometry.setAttribute('normal', this.geometry.getAttribute('normal'));
                geometry.setAttribute('uv', this.geometry.getAttribute('uv'));
                geometry.setIndex(new THREE.BufferAttribute(index3, 1));
                const box = new THREE.Box3();
                const point = new THREE.Vector3();
                for (const vertex of index3)
                {
                    box.expandByPoint(point.set(positions[vertex * 3], positions[vertex * 3 + 1], positions[vertex * 3 + 2]));
                }
                geometry.boundingBox = box;
                geometry.boundingSphere = box.getBoundingSphere(new THREE.Sphere());
                const mesh = new THREE.Mesh(geometry, this.groups[index].material);
                mesh.matrixAutoUpdate = false;
                this.world.add(mesh);
                this.terrainChunks.push({ mesh, triangles: Uint32Array.from(triangles) });
            }
        }
    }

    // --- the travel scrubber (S5b2; S5_BROWSER_EDITOR.md 3.5) -------------------------------------------------------

    // The object scrubbed: its faces drawn away from the mesh (a faint ghost stays where they are drawn, closed) and
    // a copy posed at share `t` of its travel, on the client. At 0 (as the mesh draws it) nothing is drawn over.
    private travelShown: { travel: Travel; t: number; base: Float32Array; mesh: THREE.Mesh; edges: THREE.LineSegments } | null = null;
    private travelHidden = new Set<string>();

    setTravel(travel: Travel | null, t: number): void
    {
        const share = Math.max(0, Math.min(1, t));
        if (!travel || share <= 0)
        {
            const had = this.travelHidden.size > 0;
            this.dropTravelMesh();
            if (had)
            {
                this.applyHidden();
            }
            this.dirty = true;
            return;
        }
        if (!this.travelShown || this.travelShown.travel.id !== travel.id)
        {
            this.dropTravelMesh();
            const base = this.trianglesOf(travel.id);
            if (!base)
            {
                return;
            }
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(base.length), 3));
            const mesh = new THREE.Mesh(geometry, new THREE.MeshLambertMaterial({ color: this.tokenColours.select, side: THREE.DoubleSide,
                transparent: true, opacity: 0.9 }));
            mesh.matrixAutoUpdate = false;
            const edges = new THREE.LineSegments(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.6 }));
            edges.matrixAutoUpdate = false;
            this.world.add(mesh, edges);
            this.travelShown = { travel, t: share, base, mesh, edges };
            this.travelHidden = new Set([travel.id]);
            this.applyHidden();
        }
        const shown = this.travelShown!;
        shown.travel = travel;
        shown.t = share;
        const attribute = shown.mesh.geometry.getAttribute('position') as THREE.BufferAttribute;
        poseTriangles(shown.base, travel.moves, share, attribute.array as Float32Array);
        attribute.needsUpdate = true;
        shown.mesh.geometry.computeVertexNormals();
        shown.mesh.geometry.computeBoundingSphere();
        shown.edges.geometry.dispose();
        shown.edges.geometry = new THREE.EdgesGeometry(shown.mesh.geometry, 30);
        this.dirty = true;
    }

    // The share shown now (scripted runs), or null.
    travelShare(): number | null
    {
        return this.travelShown?.t ?? null;
    }

    private dropTravelMesh(): void
    {
        if (this.travelShown)
        {
            for (const object of [this.travelShown.mesh, this.travelShown.edges])
            {
                this.world.remove(object);
                object.geometry.dispose();
                (object.material as THREE.Material).dispose();
            }
            this.travelShown = null;
        }
        this.travelHidden = new Set();
    }

    private clearMesh(): void
    {
        for (const chunk of this.terrainChunks)
        {
            chunk.mesh.geometry.dispose();
            this.world.remove(chunk.mesh);
        }
        this.terrainChunks = [];
        if (this.mainMesh)
        {
            this.world.remove(this.mainMesh);
            this.mainMesh = null;
        }
        this.geometry?.dispose();
        this.geometry = null;
        for (const group of this.groups)
        {
            group.material.dispose();
        }
        this.groups = [];
        this.liquids = [];
        this.overlays.clear();
        this.selectionOverlay = null;
        this.hoverOverlay = null;
        this.ghost = null;
        this.originalIndices = null;
    }

    private overlayFor(id: string | null, colour: THREE.Color, opacity: number): THREE.Mesh | null
    {
        if (!id || !this.geometry)
        {
            return null;
        }
        const base = this.baseIds.indexOf(id);
        if (base < 0)
        {
            return null;
        }
        const picked: number[] = [];
        for (let t = 0; t < this.triangleFaces.length; ++t)
        {
            if (this.ownerBase[this.triangleFaces[t]] === base)
            {
                picked.push(this.indices[t * 3], this.indices[t * 3 + 1], this.indices[t * 3 + 2]);
            }
        }
        if (picked.length === 0)
        {
            return null;
        }
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', this.geometry.getAttribute('position'));
        geometry.setIndex(new THREE.BufferAttribute(Uint32Array.from(picked), 1));
        const material = new THREE.MeshBasicMaterial({
            color: colour, transparent: true, opacity, depthWrite: false, side: THREE.DoubleSide,
            polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2,
        });
        const mesh = new THREE.Mesh(geometry, material);
        mesh.matrixAutoUpdate = false;
        return mesh;
    }

    private refreshOverlays(): void
    {
        for (const overlay of [this.selectionOverlay, this.hoverOverlay])
        {
            if (overlay)
            {
                this.overlays.remove(overlay);
                overlay.geometry.dispose();
                (overlay.material as THREE.Material).dispose();
            }
        }
        this.selectionOverlay = this.overlayFor(this.selectionId, this.tokenColours.select, 0.3);
        this.hoverOverlay = this.hoverId !== this.selectionId ? this.overlayFor(this.hoverId, this.tokenColours.hover, 0.25) : null;
        for (const overlay of [this.selectionOverlay, this.hoverOverlay])
        {
            if (overlay)
            {
                this.overlays.add(overlay);
            }
        }
        this.dirty = true;
    }

    private resize(): void
    {
        const width = Math.max(1, this.root.clientWidth);
        const height = Math.max(1, this.root.clientHeight);
        this.renderer.setSize(width, height, false);
        this.renderer.domElement.style.width = `${width}px`;
        this.renderer.domElement.style.height = `${height}px`;
        this.camera_.aspect = width / height;
        this.camera_.fov = studioVerticalFov(width / height);
        this.camera_.updateProjectionMatrix();
        this.placeFrameOutline(width, height);
        this.dirty = true;
    }

    // The vertical field of view in degrees (the camera check reads it).
    verticalFov(): number
    {
        return this.camera_.fov;
    }

    // Shows the outline of the game's frame (walk mode: what the game would show from here).
    setFrameShown(on: boolean): void
    {
        this.frameShown = on;
        this.placeFrameOutline(Math.max(1, this.root.clientWidth), Math.max(1, this.root.clientHeight));
    }

    private placeFrameOutline(width: number, height: number): void
    {
        const frame = gameFrameIn(width, height);
        const exact = Math.abs(frame.width - width) < 2 && Math.abs(frame.height - height) < 2;
        this.frameOutline.hidden = !this.frameShown || exact;
        Object.assign(this.frameOutline.style, { left: `${frame.left}px`, top: `${frame.top}px`, width: `${frame.width}px`,
            height: `${frame.height}px` });
    }

    private direction(): THREE.Vector3
    {
        return new THREE.Vector3(Math.cos(this.pitch) * Math.cos(this.yaw), Math.cos(this.pitch) * Math.sin(this.yaw), Math.sin(this.pitch));
    }

    private updateCamera(): void
    {
        this.pitch = Math.max(-1.55, Math.min(1.55, this.pitch));
        const direction = this.direction();
        this.camera_.position.copy(this.target).addScaledVector(direction, -this.distance);
        this.camera_.lookAt(this.target);
        this.camera_.near = Math.max(4, this.distance / 2000);
        this.camera_.far = Math.max(200000, this.distance * 20);
        this.camera_.updateProjectionMatrix();
        this.cutPlane.constant = this.target.z + 192;
        this.callbacks.onCamera?.([this.camera_.position.x, this.camera_.position.y, this.camera_.position.z]);
        this.dirty = true;
    }

    private render(): void
    {
        if (this.contextLost)
        {
            return;
        }
        const start = performance.now();
        this.scalePins();
        this.renderer.render(this.scene, this.camera_);
        this.lastFrameMs = performance.now() - start;
        this.framesDrawn += 1;
        this.dirty = false;
    }

    private readonly tick = (now: number) =>
    {
        if (!this.running)
        {
            return;
        }
        const seconds = Math.min(0.1, (now - this.lastTick) / 1000);
        this.lastTick = now;
        if (this.keys.size > 0)
        {
            this.fly(seconds);
        }
        if (this.liquids.length > 0)
        {
            const wave = 0.85 + 0.15 * Math.sin(now / 600);
            for (const material of this.liquids)
            {
                if (!material.map)
                {
                    material.color.copy(this.tokenColours.liquid).multiplyScalar(wave);
                }
            }
            this.dirty = true;
        }
        if (this.hoverQueued)
        {
            const { x, y } = this.hoverQueued;
            this.hoverQueued = null;
            this.setHover(this.pickAt(x, y), true);
        }
        if (this.dirty)
        {
            this.render();
        }
        requestAnimationFrame(this.tick);
    };

    private fly(seconds: number): void
    {
        const speed = (this.keys.has('ShiftLeft') || this.keys.has('ShiftRight') ? 3000 : 1000) * seconds;
        const forward = this.direction();
        const right = new THREE.Vector3(Math.sin(this.yaw), -Math.cos(this.yaw), 0);
        const move = new THREE.Vector3();
        if (this.keys.has('KeyW')) move.add(forward);
        if (this.keys.has('KeyS')) move.sub(forward);
        if (this.keys.has('KeyD')) move.add(right);
        if (this.keys.has('KeyA')) move.sub(right);
        if (this.keys.has('KeyE')) move.z += 1;
        if (this.keys.has('KeyQ') && this.drag?.button === 2) move.z -= 1;
        if (move.lengthSq() > 0)
        {
            this.target.addScaledVector(move.normalize(), speed);
            this.updateCamera();
        }
    }

    private setHover(pick: PickResult | null, notify: boolean): void
    {
        this.lastHover = pick;
        const id = pick?.base || null;
        this.setHoverId(id);
        if (notify)
        {
            this.callbacks.onHover(pick);
        }
    }

    private readonly onContextLost = (event: Event) =>
    {
        event.preventDefault();
        this.contextLost = true;
    };

    // The context is back: everything is uploaded again from what this module kept (no call to the core).
    private readonly onContextRestored = () =>
    {
        this.contextLost = false;
        this.contextRestores += 1;
        for (const entry of this.textures.values())
        {
            entry.texture.needsUpdate = true;
        }
        for (const group of this.groups)
        {
            const map = (group.material as THREE.MeshLambertMaterial).map;
            if (map)
            {
                map.needsUpdate = true;
            }
            group.material.needsUpdate = true;
        }
        if (this.geometry)
        {
            for (const attribute of Object.values(this.geometry.attributes))
            {
                (attribute as THREE.BufferAttribute).needsUpdate = true;
            }
            if (this.geometry.index)
            {
                this.geometry.index.needsUpdate = true;
            }
        }
        for (const chunk of this.terrainChunks)
        {
            if (chunk.mesh.geometry.index)
            {
                chunk.mesh.geometry.index.needsUpdate = true;
            }
        }
        this.refreshOverlays();
        this.dirty = true;
    };

    private readonly onPointerDown = (event: PointerEvent) =>
    {
        this.renderer.domElement.focus();
        if (this.walking)
        {
            return;
        }
        this.renderer.domElement.setPointerCapture(event.pointerId);
        this.drag = {
            x: event.clientX, y: event.clientY, button: event.button, shift: event.shiftKey, moved: false,
            yaw: this.yaw, pitch: this.pitch, target: this.target.clone(),
        };
    };

    private readonly onPointerMove = (event: PointerEvent) =>
    {
        const rect = this.renderer.domElement.getBoundingClientRect();
        const drag = this.drag;
        if (!drag)
        {
            if (!this.walking || document.pointerLockElement !== this.renderer.domElement)
            {
                this.hoverQueued = { x: event.clientX - rect.left, y: event.clientY - rect.top };
            }
            return;
        }
        const dx = event.clientX - drag.x;
        const dy = event.clientY - drag.y;
        if (!drag.moved && Math.hypot(dx, dy) < 4)
        {
            return;
        }
        drag.moved = true;
        if (drag.button === 2)
        {
            // Look: the camera stays, the target turns about it.
            const eye = this.camera_.position.clone();
            this.yaw = drag.yaw - dx * 0.004;
            this.pitch = drag.pitch - dy * 0.004;
            this.pitch = Math.max(-1.55, Math.min(1.55, this.pitch));
            this.target.copy(eye).addScaledVector(this.direction(), this.distance);
            this.updateCamera();
        }
        else if (drag.button === 1 || drag.shift)
        {
            const scale = (this.distance * Math.tan((this.camera_.fov * Math.PI) / 360) * 2) / rect.height;
            const right = new THREE.Vector3(Math.sin(this.yaw), -Math.cos(this.yaw), 0);
            const up = new THREE.Vector3().crossVectors(right, this.direction()).normalize();
            this.target.copy(drag.target).addScaledVector(right, -dx * scale).addScaledVector(up, dy * scale);
            this.updateCamera();
        }
        else
        {
            this.yaw = drag.yaw - dx * 0.006;
            this.pitch = drag.pitch - dy * 0.006;
            this.updateCamera();
        }
    };

    private readonly onPointerUp = (event: PointerEvent) =>
    {
        const drag = this.drag;
        this.drag = null;
        if (drag && !drag.moved && event.button === 0)
        {
            const rect = this.renderer.domElement.getBoundingClientRect();
            this.callbacks.onPick(this.pickAt(event.clientX - rect.left, event.clientY - rect.top));
        }
    };

    private readonly onWheel = (event: WheelEvent) =>
    {
        event.preventDefault();
        if (this.walking)
        {
            return;
        }
        this.distance = Math.max(64, Math.min(300000, this.distance * Math.exp(event.deltaY * 0.0012)));
        this.updateCamera();
    };

    private readonly onKeyDown = (event: KeyboardEvent) =>
    {
        if (this.walking)
        {
            return;
        }
        if (['KeyW', 'KeyA', 'KeyS', 'KeyD', 'KeyE', 'KeyQ', 'ShiftLeft', 'ShiftRight'].includes(event.code) && !event.ctrlKey)
        {
            // Q maximises the view unless the right button is held (fly down).
            if (event.code === 'KeyQ' && this.drag?.button !== 2)
            {
                return;
            }
            this.keys.add(event.code);
            event.stopPropagation();
        }
    };

    private readonly onKeyUp = (event: KeyboardEvent) =>
    {
        this.keys.delete(event.code);
    };

    // --- the sculpt brush's preview (S5b2, S5_BROWSER_EDITOR.md 3.18: "the client moves the mesh it has") ---------

    // The land's vertices of the mesh shown, their heights as the core built them and their nodes (row by row from
    // the north); made on the first preview of a mesh.
    private landBase: { vertices: Uint32Array; heights: Float32Array; nodes: Int32Array; mesh: THREE.BufferGeometry } | null = null;

    // The land moved by a difference per node (map units, NODES x NODES), or put back (null). The next mesh from the
    // core replaces it either way.
    previewLand(delta: Float32Array | null, size = NODES): void
    {
        const geometry = this.geometry;
        if (!geometry || !this.meta)
        {
            return;
        }
        const attribute = geometry.getAttribute('position') as THREE.BufferAttribute;
        const positions = attribute.array as Float32Array;
        if (!this.landBase || this.landBase.mesh !== geometry)
        {
            const seen = new Set<number>();
            for (const group of this.meta.groups)
            {
                if (group.kind === 'terrain')
                {
                    for (let i = group.first; i < group.first + group.count; ++i)
                    {
                        seen.add(this.indices[i]);
                    }
                }
            }
            const vertices = Uint32Array.from(seen);
            const nodes = new Int32Array(vertices.length);
            vertices.forEach((vertex, i) =>
            {
                const x = Math.round((positions[vertex * 3] + size * 256) / 512);
                const y = Math.round((size * 256 - positions[vertex * 3 + 1]) / 512);
                nodes[i] = x >= 0 && y >= 0 && x < size && y < size ? y * size + x : -1;
            });
            this.landBase = { vertices, nodes, mesh: geometry, heights: Float32Array.from(vertices, (vertex) => positions[vertex * 3 + 2]) };
        }
        const base = this.landBase;
        base.vertices.forEach((vertex, i) =>
        {
            const node = base.nodes[i];
            positions[vertex * 3 + 2] = base.heights[i] + (delta && node >= 0 ? delta[node] : 0);
        });
        attribute.needsUpdate = true;
        this.dirty = true;
    }
}
