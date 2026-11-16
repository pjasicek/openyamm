// Author mode's stages and tools (S5_BROWSER_EDITOR.md 3.2, 3.3, 3.9): stages filter the tool rail and choose the
// default view, never lock anything; each tool has one key. Indoor tools of 3.18: part 1 (shape) and part 2 (the
// placing tools of Build, Populate and Dress, and the Wire stage's link).
import type { FileTrees, Issue, JsonObject } from '../../../schema/rpc/generated/rpc.ts';
import type { ViewMode } from '../state/store.ts';

export type ToolName = 'select' | 'room' | 'corridor' | 'opening' | 'door' | 'stairs' | 'level' | 'platform' | 'pillar'
    | 'switch' | 'chest' | 'exit' | 'start' | 'spawn' | 'monster' | 'item' | 'decoration' | 'light' | 'sound' | 'placeholder' | 'link'
    // Part two: the plan's bubbles, links and goals; the blocks that move or mark a floor; the per-word tools of a room.
    | 'space' | 'planlink' | 'goal' | 'lift' | 'mover' | 'plate' | 'floor' | 'ladder' | 'points' | 'flight' | 'parapet' | 'beam'
    | 'ceiling'
    // S5b2, outdoors (OUTDOOR_TOOLS below): the land, water, roads, districts, buildings, structures, ground, people.
    | 'spots' | 'sculpt' | 'patch' | 'hpoint' | 'ridge' | 'cliff' | 'terrace' | 'cut' | 'rough' | 'peaks' | 'spire' | 'frame' | 'rim'
    | 'water' | 'river' | 'road' | 'district' | 'plot' | 'building' | 'structure' | 'ground' | 'scatter' | 'area' | 'actor' | 'arrival';

// The placing tools (3.18 "start, spawns, monsters, ..."): each makes one kind of thing of objects.yml.
export const PLACING_TOOLS: ToolName[] = ['switch', 'chest', 'exit', 'start', 'spawn', 'monster', 'item', 'decoration', 'light', 'sound', 'placeholder'];

export interface ToolInfo
{
    name: ToolName;
    label: string;
    key: string;
    // KeyboardEvent.code of the key.
    code: string;
    // The key is pressed with Shift (part two's tools: the plain letters are taken).
    shift?: boolean;
    // What it does, shown on hover, with where it is seen in a shipped map.
    help: string;
}

export const TOOLS: ToolInfo[] = [
    { name: 'select', label: 'Select', key: 'V', code: 'KeyV', help: 'Select and change: drag a selected room\'s corners and edges, double-click an edge to add a corner, PgUp/PgDn move the floor under the cursor (Shift: the ceiling).' },
    { name: 'room', label: 'Room', key: 'O', code: 'KeyO', help: 'Click the corners of a room on the plan; Enter (or a click on the first corner) finishes, Backspace takes the last corner back, Esc cancels. Snaps to the grid, to other rooms\' corners and walls and to 45°; Shift draws at any angle. As the rooms of Goblinwatch.' },
    { name: 'corridor', label: 'Corridor', key: 'C', code: 'KeyC', help: 'Click the points of a corridor\'s centre line, Enter to finish; its width is in the options. As the winding passages of the Dragoons\' Caverns.' },
    { name: 'opening', label: 'Opening', key: 'I', code: 'KeyI', help: 'Drag across the wall between two rooms, from one into the other: a doorway where the drag crosses. Width and height in the options.' },
    { name: 'door', label: 'Door', key: 'D', code: 'KeyD', help: 'Click an opening to put a door in it; the kind of door from the presets in the options (a portcullis, a sliding stone, a secret wall).' },
    { name: 'stairs', label: 'Stairs', key: 'S', code: 'KeyS', help: 'Drag across a room from its low side to its high side: the floor rises by the options\' rise toward the wall the drag points at, as steps when a step count is given.' },
    { name: 'level', label: 'Level', key: 'Y', code: 'KeyY', help: 'Inside the selected room: drag a box, or click corners and Enter, for a part of the floor at another height (a dais, a gallery, a pit when the rise is below zero).' },
    { name: 'platform', label: 'Platform', key: 'T', code: 'KeyT', help: 'Inside the selected room: drag a box (or click corners and Enter) for a block standing on the floor: a dais, an altar, a bookcase.' },
    { name: 'pillar', label: 'Pillar', key: 'X', code: 'KeyX', help: 'Inside the selected room: drag a box (or click corners and Enter) for a column from floor to ceiling.' },
    { name: 'switch', label: 'Switch', key: 'W', code: 'KeyW', help: 'Click a wall: a lever, a button or a wall plate there (kind and height in the options). Wire it to a door in the Wire stage (L). As the levers of Gharik\'s Forge.' },
    { name: 'chest', label: 'Chest', key: 'B', code: 'KeyB', help: 'Click a floor: a chest of the options\' kind, with its open event; drag it later with Select, turn it by its facing handle, fill it in the inspector (Contents).' },
    { name: 'exit', label: 'Exit', key: 'K', code: 'KeyK', help: 'Click a wall: a way out of the map to the neighbour picked in the options (make one there first), with its event.' },
    { name: 'start', label: 'Start', key: 'A', code: 'KeyA', help: 'Click where the party enters the map; turn it by its facing handle with Select.' },
    { name: 'spawn', label: 'Spawn', key: 'N', code: 'KeyN', help: 'Click: a spawn point of the map card\'s encounter slot (1 to 3) and tier from the options; its radius by the handle. As the shipped maps\' monster spawns.' },
    { name: 'monster', label: 'Monster', key: 'M', code: 'KeyM', help: 'Click: one monster standing there from the start (a guard, a boss), named in the options by its number or name in monster_data.txt.' },
    { name: 'item', label: 'Item', key: 'U', code: 'KeyU', help: 'Click: an item lying on the floor (its number or name in the options).' },
    { name: 'decoration', label: 'Decoration', key: 'E', code: 'KeyE', help: 'Click a floor for a standing decoration, or a wall for one that hangs there (a torch in its sconce): the decoration from the options or dragged from the Library.' },
    { name: 'light', label: 'Light', key: 'H', code: 'KeyH', help: 'Click: a light at the options\' radius and height; its radius by the handle.' },
    { name: 'sound', label: 'Sound', key: 'Z', code: 'KeyZ', help: 'Click: an ambient sound (the world\'s sound file named in the options) heard within its radius.' },
    { name: 'placeholder', label: 'Placeholder', key: 'J', code: 'KeyJ', help: 'Click: a mark for a thing no asset exists for yet, in words an artist can use.' },
    { name: 'link', label: 'Link', key: 'L', code: 'KeyL', help: 'With a switch, plate or door selected: L, then click the doors (and levers) it moves. Each click adds the target to the source\'s event (made when it has none) as the options\' verb; a second click takes it out. Esc ends.' },
    { name: 'space', label: 'Space', key: '⇧S', code: 'KeyS', shift: true, help: 'Plan: click an empty place for a planned space (a bubble of the options\' kind and size); drag a bubble to move it. A room drawn over a bubble realises its space. As the bubble diagrams of the briefs.' },
    { name: 'planlink', label: 'Plan link', key: '⇧K', code: 'KeyK', shift: true, help: 'Plan: drag from one space to another: how they connect (the options\' kind: open, door, stairs, lift ...); a link\'s lock goes in the inspector.' },
    { name: 'goal', label: 'Goal', key: '⇧G', code: 'KeyG', shift: true, help: 'Plan: click a space: a goal there (reach, take, kill, use or set, and what, from the options).' },
    { name: 'lift', label: 'Lift', key: '⇧F', code: 'KeyF', shift: true, help: 'Drag a box in a room: a block of floor an event raises by the options\' travel (a lift, as the Hive\'s). Wire it with L from a switch.' },
    { name: 'mover', label: 'Mover', key: '⇧M', code: 'KeyM', shift: true, help: 'Drag a box (or click corners and Enter) in a room: a block that travels by the options\' [x, y, z] when its event fires (a bridge that slides out, a wall that sinks).' },
    { name: 'plate', label: 'Plate', key: '⇧P', code: 'KeyP', shift: true, help: 'Drag a box in a room: a pressure plate the party steps on (wire it: select it, L, click the doors it moves).' },
    { name: 'floor', label: 'Floor', key: '⇧W', code: 'KeyW', shift: true, help: 'Click a room\'s floor, a level, a platform or a plate: it becomes lava, water or liquid (the options\' kind). A level or platform without an id gets one from the core first.' },
    { name: 'ladder', label: 'Ladder', key: '⇧L', code: 'KeyL', shift: true, help: 'Drag from the foot of a ladder up onto what it climbs (a level, a platform, the next room\'s higher floor): the ladder stands against its edge, as high as the climb.' },
    { name: 'points', label: 'Height points', key: '⇧H', code: 'KeyH', shift: true, help: 'In a room: click to add a point of an uneven floor (or ceiling, in the options) at the options\' height; drag a point; PgUp/PgDn over a point raise or lower it; Alt click removes it. As the shipped caves.' },
    { name: 'flight', label: 'Flight', key: '⇧T', code: 'KeyT', shift: true, help: 'In a room: drag from a point on the lower floor to the edge of the higher one (a level or platform): steps between them.' },
    { name: 'parapet', label: 'Parapet', key: '⇧R', code: 'KeyR', shift: true, help: 'In a room: click the points of a low wall (a gallery\'s rim, a balustrade), Enter to finish; its height in the options.' },
    { name: 'beam', label: 'Beam', key: '⇧B', code: 'KeyB', shift: true, help: 'In a room: click the points of a bar that hangs under the ceiling (a rafter, a lintel), Enter to finish; width, depth and its underside in the options.' },
    { name: 'ceiling', label: 'Ceiling level', key: '⇧C', code: 'KeyC', shift: true, help: 'In a room: drag a box (or click corners and Enter) for a part of the ceiling that lies higher (a dome\'s drum, a coffer, a lantern): the options\' rise above the room\'s ceiling.' },
];

export function toolInfo(name: ToolName): ToolInfo
{
    return TOOLS.find((tool) => tool.name === name) ?? OUTDOOR_TOOLS.find((tool) => tool.name === name) ?? TOOLS[0];
}

export interface StageInfo
{
    number: number;
    name: string;
    tools: ToolName[];
    view: ViewMode;
    // What the stage is done when (3.3).
    done: string;
}

export const STAGES: StageInfo[] = [
    { number: 1, name: 'Plan', tools: ['select', 'space', 'planlink', 'goal'], view: 'plan', done: 'every space named with a purpose; the critical path reaches the goals' },
    { number: 2, name: 'Shape', tools: ['select', 'room', 'corridor', 'opening', 'stairs', 'level', 'platform', 'pillar', 'points', 'flight', 'parapet', 'beam', 'ceiling'], view: 'split', done: 'every planned space has a room; every room reached' },
    { number: 3, name: 'Build', tools: ['select', 'door', 'opening', 'platform', 'pillar', 'switch', 'chest', 'exit', 'lift', 'mover', 'plate', 'floor', 'ladder'], view: 'split', done: 'no grey faces; every planned door exists' },
    { number: 4, name: 'Wire', tools: ['select', 'link'], view: 'board', done: 'no unbound clicked face; the solve opens everything planned' },
    { number: 5, name: 'Populate', tools: ['select', 'start', 'spawn', 'monster', 'item', 'chest'], view: 'plan', done: 'density and sizes within the shipped bands' },
    { number: 6, name: 'Dress', tools: ['select', 'light', 'decoration', 'sound', 'placeholder'], view: 'split', done: 'nothing floats or clips' },
    { number: 7, name: 'Test', tools: ['select'], view: 'split', done: 'the checklist and the issue list are empty' },
];

function list(files: FileTrees, file: keyof FileTrees, name: string): JsonObject[]
{
    const value = files[file]?.tree[name];
    return Array.isArray(value) ? (value as JsonObject[]) : [];
}

// What each stage counts (3.3: "a count of what is open in it"), as short text: done of wanted where the plan says
// what is wanted, else how many there are.
export function stageCounts(files: FileTrees | undefined, issues: readonly Issue[]): Record<number, string>
{
    if (!files)
    {
        return {};
    }
    const spaces = list(files, 'plan.yml', 'spaces');
    const rooms = list(files, 'rooms.yml', 'rooms');
    const realised = new Set(rooms.map((room) => String(room.space ?? room.id)));
    const openings = list(files, 'rooms.yml', 'openings');
    const doors = list(files, 'objects.yml', 'doors');
    const events = list(files, 'wiring.yml', 'events');
    const switches = list(files, 'objects.yml', 'switches');
    const populate = ['spawns', 'monsters', 'items', 'chests'].reduce((sum, name) => sum + list(files, 'objects.yml', name).length, 0);
    const dress = ['lights', 'decorations', 'sounds'].reduce((sum, name) => sum + list(files, 'objects.yml', name).length, 0);
    const errors = issues.filter((issue) => issue.severity === 'error').length;
    return {
        1: spaces.length > 0 ? `${spaces.length}` : '—',
        2: spaces.length > 0 ? `${spaces.filter((space) => realised.has(String(space.id))).length}/${spaces.length}` : `${rooms.length}`,
        3: openings.length > 0 ? `${doors.length}/${openings.length}` : '0',
        4: `${events.length}/${switches.length + doors.length}`,
        5: `${populate}`,
        6: `${dress}`,
        7: errors > 0 ? `${errors}` : 'ok',
    };
}

// Tool options (3.9): the active tool's settings, never the selection's properties.
export interface ToolOptions
{
    grid: number;
    snap: boolean;
    floor: number;
    ceiling: number;
    width: number;
    openingWidth: number;
    openingHeight: number;
    door: string;
    rise: number;
    steps: number;
    levelRise: number;
    platformRise: number;
    // The placing tools (part 2).
    switchKind: 'lever' | 'button' | 'plate';
    // Above the floor; 0: the kind's default.
    switchHeight: number;
    chestKind: string;
    // The chest's and the exit's own event (preset chest, exit) made with them.
    withEvent: boolean;
    exitTo: string;
    spawnSlot: number;
    spawnTier: 'a' | 'b' | 'c';
    spawnRadius: number;
    monster: string;
    item: string;
    decoration: string;
    // A decoration clicked on a wall hangs this high.
    wallHeight: number;
    lightRadius: number;
    // 0: the core's default (three quarters of the room's height).
    lightHeight: number;
    sound: string;
    soundRadius: number;
    standsFor: string;
    // What the link tool writes: the verb of the source's event.
    linkVerb: 'toggles' | 'opens' | 'closes';
    // A plan space the next room drawn realises (from the Checklist).
    space: string;
    // Part two. The Plan stage: a new space's kind and size, a link's kind, a goal's kind and what.
    spaceKind: string;
    spaceSize: string;
    planLinkKind: string;
    goalKind: 'reach' | 'take' | 'kill' | 'use' | 'set';
    goalWhat: string;
    // Lifts: how far they rise; movers: their block's height and travel [x, y, z]; plates: how far they stand up.
    liftTravel: number;
    moverHeight: number;
    moverTravelX: number;
    moverTravelY: number;
    moverTravelZ: number;
    plateRise: number;
    floorKind: 'lava' | 'water' | 'liquid';
    // A ladder's height when the drag's end finds no higher floor (0: the climb measured).
    ladderHeight: number;
    // Height points: on the floor or the ceiling, at this height (absolute z; the room's own height when the
    // point is first made unless set), changed by this step with PgUp and PgDn.
    pointsOn: 'floor' | 'ceiling';
    pointHeight: number;
    pointStep: number;
    parapetHeight: number;
    beamWidth: number;
    beamDepth: number;
    // The beam's underside above the room's floor (0: the depth and 32 under the ceiling).
    beamBottom: number;
    // A ceiling level's rise above the room's ceiling.
    ceilingRise: number;
    // S5b2: the outdoor tools' settings.
    outdoor: OutdoorOptions;
}

// The outdoor tools' settings (3.9): heights in map units, sizes in cells.
export interface OutdoorOptions
{
    // The land words' height (a ridge's, a terrace's, a cut's floor, a height point's, a spire's, a level rim's).
    height: number;
    // PgUp and PgDn on a height under the cursor (a point, a terrace, a road's bed).
    heightStep: number;
    // Points on half cells everywhere (else whole cells; Shift while clicking: half).
    halfCells: boolean;
    // The grid editor: the height a click or a drag paints.
    spotHeight: number;
    brushMode: 'raise' | 'lower' | 'smooth' | 'flatten';
    // Cells.
    brushRadius: number;
    // Map units a dab at the brush's middle (raise, lower).
    brushStrength: number;
    ridgeWidth: number;
    ridgeSlope: number;
    terraceSlope: number;
    cliffDrop: number;
    cliffDown: 'left' | 'right';
    roughAmount: number;
    peaksCount: number;
    peaksLow: number;
    peaksHigh: number;
    rimForm: 'level' | 'ridge';
    waterKind: 'pond' | 'lake' | 'inlet' | 'sea';
    // 0: a step under the lowest land on the outline.
    waterLevel: number;
    tileSet: string;
    riverWidth: number;
    roadWidth: 'lane' | 'road' | 'high_road';
    roadSurface: string;
    // A road's points step square or at 45 degrees.
    roadSteps: boolean;
    // '' a new district space.
    districtSpace: string;
    districtName: string;
    plotBuilding: string;
    plotFacing: 'n' | 'e' | 's' | 'w';
    roof: string;
    roofPitch: number;
    facing: 'n' | 'e' | 's' | 'w';
    kit: string;
    structureKind: string;
    groundMaterial: string;
    groundRadius: number;
    decoration: string;
    scatterCount: number;
    scatterSpacing: number;
    scatterLine: boolean;
    areaKind: 'encounter' | 'items' | 'keep_clear' | 'open';
    areaCircle: boolean;
    areaSlot: number;
    areaCount: number;
    // A plan population, or the name of a new one.
    areaPopulation: string;
    monster: string;
    actorCount: number;
    actorHostile: boolean;
    pointKind: 'entrance' | 'landmark';
    pointFacing: 'n' | 'ne' | 'e' | 'se' | 's' | 'sw' | 'w' | 'nw';
}

export const DEFAULT_OUTDOOR: OutdoorOptions = {
    height: 384,
    heightStep: 32,
    halfCells: false,
    spotHeight: 384,
    brushMode: 'raise',
    brushRadius: 3,
    brushStrength: 48,
    ridgeWidth: 2,
    ridgeSlope: 4,
    terraceSlope: 2,
    cliffDrop: 384,
    cliffDown: 'right',
    roughAmount: 48,
    peaksCount: 6,
    peaksLow: 768,
    peaksHigh: 1536,
    rimForm: 'level',
    waterKind: 'pond',
    waterLevel: 0,
    tileSet: '',
    riverWidth: 1,
    roadWidth: 'road',
    roadSurface: 'pebbles',
    roadSteps: true,
    districtSpace: '',
    districtName: 'Town',
    plotBuilding: '',
    plotFacing: 's',
    roof: 'hip',
    roofPitch: 0,
    facing: 's',
    kit: '',
    structureKind: 'well',
    groundMaterial: 'sand',
    groundRadius: 3,
    decoration: 'tree12',
    scatterCount: 20,
    scatterSpacing: 2,
    scatterLine: false,
    areaKind: 'encounter',
    areaCircle: false,
    areaSlot: 1,
    areaCount: 3,
    areaPopulation: 'monsters',
    monster: 'Peasant',
    actorCount: 1,
    actorHostile: false,
    pointKind: 'entrance',
    pointFacing: 's',
};

export const DEFAULT_OPTIONS: ToolOptions = {
    grid: 64,
    snap: true,
    floor: 0,
    ceiling: 384,
    width: 256,
    openingWidth: 192,
    openingHeight: 256,
    door: 'wooden',
    rise: 128,
    steps: 0,
    levelRise: 64,
    platformRise: 64,
    switchKind: 'lever',
    switchHeight: 0,
    chestKind: 'ch1',
    withEvent: true,
    exitTo: '',
    spawnSlot: 1,
    spawnTier: 'a',
    spawnRadius: 128,
    monster: '',
    item: '',
    decoration: 'torch01',
    wallHeight: 144,
    lightRadius: 640,
    lightHeight: 0,
    sound: '',
    soundRadius: 1024,
    standsFor: '',
    linkVerb: 'toggles',
    space: '',
    spaceKind: 'room',
    spaceSize: 'M',
    planLinkKind: 'open',
    goalKind: 'reach',
    goalWhat: '',
    liftTravel: 256,
    moverHeight: 32,
    moverTravelX: 0,
    moverTravelY: 0,
    moverTravelZ: 128,
    plateRise: 0,
    floorKind: 'lava',
    ladderHeight: 0,
    pointsOn: 'floor',
    pointHeight: 64,
    pointStep: 16,
    parapetHeight: 48,
    beamWidth: 32,
    beamDepth: 32,
    beamBottom: 0,
    ceilingRise: 128,
    outdoor: DEFAULT_OUTDOOR,
};

export const CHEST_KINDS = ['ch1', 'ch2', 'ch3', 'ch4', 'ch5', 'ch001', 'ch002', 'ch003', 'ch004', 'ch005', 'ch006', '7gt002', 'gt002'];

export const GRIDS = [8, 16, 32, 64, 128, 256, 512];

export function nextGrid(grid: number, direction: 1 | -1): number
{
    const index = GRIDS.indexOf(grid);
    const at = index < 0 ? GRIDS.indexOf(64) : index;
    return GRIDS[Math.max(0, Math.min(GRIDS.length - 1, at + direction))];
}

// --- outdoors (S5b2; S5_BROWSER_EDITOR.md 3.3's Outdoor column, 3.18's Outdoor table) ------------------------------


// The structures' kinds the generic Structure tool places (a building has its own tool; a model comes whole from a
// shipped map in the inspector).
export const STRUCTURE_KINDS = ['well', 'fountain', 'sign', 'obelisk', 'chest', 'crate', 'platform', 'stairs', 'wall', 'fence', 'barrier', 'bridge', 'walkway',
    'deck', 'doorway', 'cave_mouth', 'hatch', 'culvert', 'waterfall', 'portal', 'arch', 'stone_ring', 'trilithon', 'tent', 'arcade', 'decoration'];

export const OUTDOOR_TOOLS: ToolInfo[] = [
    { name: 'select', label: 'Select', key: 'V', code: 'KeyV', help: 'Select and change: a click selects a word of the sketch; drag its points, a box\'s corners or the whole of it; double-click an edge to add a point, a building to enter it (its parts); Alt click a point takes it out; PgUp/PgDn change the height under the cursor (a point, a terrace, a ridge, a road\'s bed at its nearest point).' },
    { name: 'spots', label: 'Spot heights', key: 'H', code: 'KeyH', help: 'The grid editor: every spot height of heights.grid a handle with its number. Click or drag paints the options\' height over the spots; PgUp/PgDn on the hovered spot raise or lower it one unit; Alt click takes its height. As the briefs\' coarse land.' },
    { name: 'sculpt', label: 'Sculpt', key: 'B', code: 'KeyB', help: 'The brush (raise, lower, smooth, flatten; radius and strength in the options): shown while you drag, written once when you let go. On land agents describe only inside a sculpt patch (Patch); anywhere once the land is marked made by hand (Project settings).' },
    { name: 'patch', label: 'Patch', key: '⇧P', code: 'KeyP', shift: true, help: 'A sculpt patch: drag a box or click an outline (at most 32 cells each way, 16 patches): the bounded, marked place a person sculpts on land the sketch describes.' },
    { name: 'hpoint', label: 'Height point', key: '⇧H', code: 'KeyH', shift: true, help: 'Click a node: a height point at the options\' height (peaks, passes, plazas); PgUp/PgDn with Select change it.' },
    { name: 'ridge', label: 'Ridge', key: 'R', code: 'KeyR', help: 'Click the points of a ridge\'s crest (a dyke, a ledge), Enter: the options\' height, width and slope.' },
    { name: 'cliff', label: 'Cliff', key: 'C', code: 'KeyC', help: 'Click the points of a cliff\'s edge, Enter: the land falls by the options\' drop to its low side (ticks).' },
    { name: 'terrace', label: 'Terrace', key: 'T', code: 'KeyT', help: 'Drag a box or click an outline: level land at the options\' height (a town\'s terrace), the land outside running back over the slope.' },
    { name: 'cut', label: 'Cut', key: 'X', code: 'KeyX', help: 'Drag a box or click an outline: a hollow with sheer walls, its floor at the options\' height.' },
    { name: 'rough', label: 'Rough', key: '⇧R', code: 'KeyR', shift: true, help: 'Drag a box or click an outline: ground made rougher by the options\' amount.' },
    { name: 'peaks', label: 'Peaks', key: 'K', code: 'KeyK', help: 'Drag a box or click an outline: an area of peaks (count and height range in the options).' },
    { name: 'spire', label: 'Spire', key: '⇧S', code: 'KeyS', shift: true, help: 'Click a node: a sheer needle of rock at the options\' height.' },
    { name: 'frame', label: 'Frame', key: '⇧F', code: 'KeyF', shift: true, help: 'Drag the square the party can walk (frame.playable); its corners with Select.' },
    { name: 'rim', label: 'Rim', key: '⇧E', code: 'KeyE', shift: true, help: 'Drag along a side of the map: a stretch of rim there (level land or a ridge of tops, in the options).' },
    { name: 'water', label: 'Water', key: 'W', code: 'KeyW', help: 'Drag a box or click an outline: a pond, a lake or a sea (kind and level in the options), with its plan space.' },
    { name: 'river', label: 'River', key: '⇧W', code: 'KeyW', shift: true, help: 'Click a river\'s middle line from its source down, Enter: with its plan space.' },
    { name: 'road', label: 'Road', key: 'O', code: 'KeyO', help: 'Click cells: the road steps square or at 45 degrees as the road tiles lay; Enter makes it with its plan link. Drag its points with Select; PgUp/PgDn over a point set its bed.' },
    { name: 'district', label: 'District', key: 'I', code: 'KeyI', help: 'Drag a box or click an outline: a district (the outline of a plan space; a new one, or the options\' space).' },
    { name: 'plot', label: 'Plot', key: '⇧I', code: 'KeyI', shift: true, help: 'Click in a district: a plot for the options\' plan building, its north-west corner there, its front on the options\' side. Move it by its corner with Select.' },
    { name: 'building', label: 'Building', key: 'U', code: 'KeyU', help: 'Drag a box: a building on that ground with its first part (the world\'s ordinary house). With a building selected, a box inside it is a new part (an L, a wing). Double-click a building with Select to enter it; its wall bays and door in the inspector.' },
    { name: 'structure', label: 'Structure', key: 'S', code: 'KeyS', help: 'The options\' kind placed by its geometry: a click for a well, a fountain, a sign or an obelisk; points and Enter for a wall, a fence, a bridge; an outline for a deck. The inspector holds the rest of its words.' },
    { name: 'ground', label: 'Ground', key: '⇧G', code: 'KeyG', shift: true, help: 'The ground brush: paint the options\' kind of land; strokes are merged per kind into zone outlines (dirt and two more kinds a map).' },
    { name: 'scatter', label: 'Scatter', key: 'N', code: 'KeyN', help: 'Drag a box or click an outline (or a row: a line, in the options): the options\' decoration, count and spacing; the build places them. A decoration dropped from the Library sets it.' },
    { name: 'area', label: 'Area', key: 'E', code: 'KeyE', help: 'Click an outline (or drag a circle, in the options): an encounter area of a plan population (made with it), items, or ground kept clear.' },
    { name: 'actor', label: 'Actor', key: 'M', code: 'KeyM', help: 'Click: the options\' monster standing there from the start (townsfolk, guards, a camp); a monster dropped from the Library goes there.' },
    { name: 'arrival', label: 'Point', key: 'A', code: 'KeyA', help: 'Click a node: an arrival point (with its plan entrance) or a landmark.' },
];

export const OUTDOOR_STAGES: StageInfo[] = [
    { number: 1, name: 'Plan', tools: ['select'], view: 'plan', done: 'every zone named with a purpose' },
    { number: 2, name: 'Shape', tools: ['select', 'spots', 'sculpt', 'patch', 'hpoint', 'ridge', 'cliff', 'terrace', 'cut', 'rough', 'peaks', 'spire', 'frame', 'rim', 'water', 'river', 'road'],
        view: 'split', done: 'the land, the water and the roads in place' },
    { number: 3, name: 'Build', tools: ['select', 'building', 'structure', 'district', 'plot', 'road', 'ground'], view: 'split', done: 'every planned building exists' },
    { number: 4, name: 'Wire', tools: ['select'], view: 'split', done: 'every door leads somewhere; what clicks says something' },
    { number: 5, name: 'Populate', tools: ['select', 'area', 'actor', 'arrival'], view: 'plan', done: 'density within the shipped bands' },
    { number: 6, name: 'Dress', tools: ['select', 'scatter', 'ground', 'structure'], view: 'split', done: 'town feel inside its ranges' },
    { number: 7, name: 'Test', tools: ['select'], view: 'split', done: 'the checklist and the issue list are empty' },
];

// The stages and tools of a project's kind.
export function stagesOf(outdoor: boolean): StageInfo[]
{
    return outdoor ? OUTDOOR_STAGES : STAGES;
}

export function toolsOf(outdoor: boolean): ToolInfo[]
{
    return outdoor ? OUTDOOR_TOOLS : TOOLS;
}

// What each outdoor stage counts.
export function outdoorStageCounts(files: FileTrees | undefined, issues: readonly Issue[]): Record<number, string>
{
    const sketch = files?.['sketch.yml']?.tree;
    if (!sketch)
    {
        return {};
    }
    const count = (value: unknown) => (Array.isArray(value) ? value.length : 0);
    const heights = (sketch.heights ?? {}) as Record<string, unknown>;
    const water = (sketch.water ?? {}) as Record<string, unknown>;
    const land = ['points', 'ridges', 'cliffs', 'terraces', 'cuts', 'rough', 'peaks', 'spires', 'strokes', 'smooth'].reduce((sum, name) => sum + count(heights[name]), 0);
    const structures = Array.isArray(sketch.structures) ? sketch.structures as Record<string, unknown>[] : [];
    const buildings = structures.filter((entry) => entry.kind === 'building').length;
    const events = count(sketch.events) + structures.filter((entry) => entry.house !== undefined || entry.effects !== undefined || entry.into !== undefined).length;
    const errors = issues.filter((issue) => issue.severity === 'error').length;
    return {
        1: `${count(files?.['plan.yml']?.tree.spaces)}`,
        2: `${land + count(water.bodies) + count(water.rivers) + count(sketch.roads)}`,
        3: `${buildings}/${structures.length}`,
        4: `${events}`,
        5: `${count(sketch.areas) + count(sketch.actors)}`,
        6: `${count(sketch.scatter) + count(sketch.ground)}`,
        7: errors > 0 ? `${errors}` : 'ok',
    };
}
