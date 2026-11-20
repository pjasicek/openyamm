#!/usr/bin/env python3
"""Pictures of every building of an outdoor rebuild beside the same building of the original, from the same cameras.

  building_shots.py <rebuild.odm> --original <orig.odm> --world <world> --assets <root of the rebuild> --out <dir>
                    [--orig-assets <root>] [--build <build.json>] [--places <places.yml>] [--only <id,id>]
                    [--time HH:MM] [--no-game] [--plan] [--mount <folder>]

--mount: the rebuild is installed in that mount folder (`oymap install --mount`; the studio host's job uses the
project's own play mount) and read in front of --assets, as the game's --extra-mount reads it; the rebuild's map
name is then looked for in <mount>/worlds/<world>/maps/. <dir>/index.json lists what index.txt lists, for the
studio's Pictures (schema/rpc/jobs.rpc.json).

<rebuild.odm> is the installed rebuild (a path, or a map name read from <assets>/worlds/<world>/maps/); <orig.odm>
likewise from --orig-assets (default assets_dev). --build is the rebuild's build.json (default: build.json beside a
rebuild path given as a file, else `build/build.json` two folders up is not guessed: pass it).

The buildings: every entry of build.json's `buildings` (its model is the bmodel of the same name in the rebuild),
then every other rebuild bmodel at least 512 across and 256 high (walls, docks, fountains, ships), then every
original bmodel of that size that no rebuild thing overlaps ("orig:<name>"). Each rebuild thing takes the original
bmodels whose plan box overlaps its own (grown by 64) as its counterpart.

The views, in the same place in both maps: `door` (and `door2`... ) in front of each rebuild door, facing it; `odoorN`
in front of an original door face (a face with an event) where no rebuild door stands within 384; `n`, `e`, `s`, `w`
from each side of the union of both maps' boxes, at eye height and raised (`n_up` ...: 640 higher, looking down at
the middle). A camera is moved nearer or sideways until nothing stands between it and the building (other bmodels'
boxes and decorations of both maps, and the terrain), and is never inside a bmodel box or a decoration; a view with
no clear place is skipped and listed. Camera z is the higher of the two terrains there (feet; the game adds the eye).

--places: `places: [{name, at: [x, y, z], yaw (rad), pitch (deg)}]`, extra views taken as given (a user's walk).

Runs one screenshot tour per map (`tools/run_game.sh --isolated`, SDL_AUDIODRIVER=dummy, one game at a time; HUD,
actors and effects off, clear weather, the same hour) and writes <dir>/<building>/<view>.jpg (original left,
rebuild right), <dir>/<building>/contact.jpg, <dir>/places/<name>.jpg, <dir>/index.html and <dir>/index.txt (every
building, its counterpart, views taken and skipped). --plan writes the tours only; --no-game makes the pairs again
from the pictures in <dir>/raw/.
"""
import html
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

studio = Path(__file__).resolve().parents[1]
repo = studio.parent
oymap = os.environ.get('OYMAP', str(studio / 'build/oymap'))

EYE = 0             # the tour's z is the party's feet
RAISE = 640
PAD = 64
MIN_BUILDING = 512  # across, for things that are not build.json buildings
MIN_HEIGHT = 256
HALF_FOV = math.radians(30)  # half the narrower horizontal view, with margin
DECO_RADIUS = {'tree': 160, 'default': 72}


def take_option(arguments, name, default=None):
    if name in arguments:
        at = arguments.index(name)
        value = arguments[at + 1]
        del arguments[at:at + 2]
        return value
    return default


def take_flag(arguments, name):
    if name in arguments:
        arguments.remove(name)
        return True
    return False


def map_path(name, root, world):
    path = Path(name)
    if path.is_file():
        return path.resolve()
    path = Path(root) / 'worlds' / world / 'maps' / Path(name).name
    if not path.is_file():
        sys.exit(f'{name}: no such map (looked in {path.parent})')
    return path.resolve()


def export(path, out):
    if not out.is_file() or out.stat().st_mtime < path.stat().st_mtime:
        done = subprocess.run([oymap, 'export', str(path), '--out', str(out)], capture_output=True, text=True)
        if done.returncode != 0:
            sys.exit(f'oymap export {path} failed: {done.stderr.strip()}')
    return json.loads(out.read_text())['map']


class Side:
    """One map: its bmodels' boxes, door faces, decorations and terrain."""

    def __init__(self, data):
        terrain = data['terrain']
        self.heights = terrain['height_map']
        self.scale = terrain.get('height_scale', 32)
        self.models = []
        for model in data['bmodels']:
            vertices = model['vertices']
            if not vertices:
                continue
            xs, ys, zs = zip(*vertices)
            doors = []
            for face in model['faces']:
                if face.get('cog_triggered'):
                    points = [vertices[i] for i in face['vertices']]
                    nx, ny, nz = (value / 65536 for value in face['plane_normal'])
                    if abs(nz) > 0.5:
                        continue
                    doors.append({'event': face['cog_triggered'],
                                  'at': [sum(p[k] for p in points) / len(points) for k in range(3)],
                                  'floor': min(p[2] for p in points), 'normal': [nx, ny]})
            self.models.append({'name': model['name'], 'box': [min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)],
                                'doors': doors})
        self.decorations = []
        for entity in data.get('entities', []):
            name = entity['name'].lower()
            radius = DECO_RADIUS['tree'] if 'tree' in name else DECO_RADIUS['default']
            self.decorations.append((entity['position'], radius, name))

    def ground(self, x, y):
        cx = min(127, max(0, int(math.floor(x / 512 + 64))))
        cy = min(127, max(0, int(math.floor(64 - y / 512))))
        return self.heights[cy * 128 + cx] * self.scale


def overlaps(a, b, grow=0):
    return a[0] - grow < b[3] and b[0] - grow < a[3] and a[1] - grow < b[4] and b[1] - grow < a[4]


def union(boxes):
    return [min(b[0] for b in boxes), min(b[1] for b in boxes), min(b[2] for b in boxes),
            max(b[3] for b in boxes), max(b[4] for b in boxes), max(b[5] for b in boxes)]


def segment_hits_box(p, q, box):
    """Slab test of the segment p-q against a 3D box."""
    t0, t1 = 0.0, 1.0
    for k in range(3):
        d = q[k] - p[k]
        lo, hi = box[k], box[k + 3]
        if abs(d) < 1e-9:
            if p[k] < lo or p[k] > hi:
                return False
            continue
        a, b = (lo - p[k]) / d, (hi - p[k]) / d
        if a > b:
            a, b = b, a
        t0, t1 = max(t0, a), min(t1, b)
        if t0 > t1:
            return False
    return True


def segment_near_point(p, q, point, radius):
    dx, dy = q[0] - p[0], q[1] - p[1]
    length = dx * dx + dy * dy
    t = 0.0 if length == 0 else max(0.0, min(1.0, ((point[0] - p[0]) * dx + (point[1] - p[1]) * dy) / length))
    x, y = p[0] + t * dx, p[1] + t * dy
    z = p[2] + t * (q[2] - p[2])
    return math.hypot(point[0] - x, point[1] - y) < radius and z < point[2] + 600


class Scene:
    def __init__(self, original, rebuilt):
        self.sides = (original, rebuilt)

    def ground(self, x, y):
        return max(side.ground(x, y) for side in self.sides)

    def blocked(self, camera, target, own, building):
        """Why the view camera -> target is not clear, or None. Decorations inside the building's box are its own."""
        for side_index, side in enumerate(self.sides):
            for model in side.models:
                if (side_index, model['name']) in own:
                    continue
                box = model['box']
                if box[5] - box[2] < 48 and box[5] < camera[2] - 32:
                    continue  # flat things under the eye (plates, pads) do not hide anything
                grown = [box[0] - 24, box[1] - 24, box[2], box[3] + 24, box[4] + 24, box[5] + 24]
                if box[0] - 40 <= camera[0] <= box[3] + 40 and box[1] - 40 <= camera[1] <= box[4] + 40 \
                        and box[2] - 64 <= camera[2] + 160 <= box[5] + 64:
                    return f'inside {"orig" if side_index == 0 else "rebuild"} {model["name"]}'
                if segment_hits_box(camera, target, grown):
                    return f'behind {"orig" if side_index == 0 else "rebuild"} {model["name"]}'
            for position, radius, name in side.decorations:
                if building[0] - 128 < position[0] < building[3] + 128 \
                        and building[1] - 128 < position[1] < building[4] + 128:
                    continue
                if math.hypot(position[0] - camera[0], position[1] - camera[1]) < radius + 48:
                    return f'in {name}'
                if segment_near_point(camera, target, position, radius):
                    return f'behind {name}'
        for step in range(1, 18):
            t = step / 20
            x = camera[0] + t * (target[0] - camera[0])
            y = camera[1] + t * (target[1] - camera[1])
            z = camera[2] + 120 + t * (target[2] - camera[2] - 120)
            if self.ground(x, y) > z:
                return 'behind the land'
        return None


def yaw_to(camera, target):
    return math.atan2(target[1] - camera[1], target[0] - camera[0])


def pitch_to(camera, target, eye=160):
    distance = math.hypot(target[0] - camera[0], target[1] - camera[1])
    return max(-40.0, min(25.0, math.degrees(math.atan2(target[2] - camera[2] - eye, max(distance, 1)))))


def place_view(scene, own, box, target, direction, distance, lateral_axis, lateral_span, raised):
    """The first clear camera: at distance, then nearer, each also shifted sideways."""
    tried = []
    for fraction in (1.0, 0.8, 0.62, 0.48, 0.36):
        for shift in (0.0, 0.25, -0.25, 0.5, -0.5):
            d = max(384.0, distance * fraction)
            x = target[0] + direction[0] * d + lateral_axis[0] * shift * lateral_span
            y = target[1] + direction[1] * d + lateral_axis[1] * shift * lateral_span
            z = scene.ground(x, y) + EYE + (RAISE if raised else 0)
            camera = [x, y, z]
            why = scene.blocked([x, y, z + 160], target, own, box)
            if why is None:
                return camera, None
            tried.append(why)
    return None, tried[0]


def gather(original, rebuilt, build):
    """Things to picture: [{id, title, rebuilt: [names], original: [names], doors: [...], box}]."""
    things = []
    used_rebuilt = set()
    by_name = {}
    for model in rebuilt.models:
        by_name.setdefault(model['name'], []).append(model)
    for building in build.get('buildings', []):
        name = building['id']
        if name not in by_name:
            continue
        used_rebuilt.add(name)
        things.append({'id': name.split(':', 1)[-1], 'title': building.get('title', ''), 'rebuilt': [name],
                       'doors': [{'at': building['door'], 'normal': building['normal'], 'floor': building['floor']}]})
    for name, models in by_name.items():
        if name in used_rebuilt:
            continue
        box = union([m['box'] for m in models])
        if max(box[3] - box[0], box[4] - box[1]) >= MIN_BUILDING and box[5] - box[2] >= MIN_HEIGHT:
            # a big thing touching one already listed (a castle's front, a bridge's ramps) is pictured with it
            host = next((t for t in things if overlaps(union([m['box'] for n in t['rebuilt'] for m in by_name[n]]),
                                                         box, PAD)), None)
            if host is not None:
                host['rebuilt'].append(name)
            else:
                things.append({'id': name.split(':', 1)[-1], 'title': '', 'rebuilt': [name], 'doors': []})
    matched = set()
    for thing in things:
        box = union([m['box'] for name in thing['rebuilt'] for m in by_name[name]])
        thing['original'] = sorted({m['name'] for m in original.models if overlaps(m['box'], box, PAD)
                                    and m['box'][5] - m['box'][2] >= 32})
        matched.update(thing['original'])
    for model in original.models:
        box = model['box']
        if model['name'] in matched or any(overlaps(box, m['box']) and m['box'][5] - m['box'][2] >= 32
                                           for m in rebuilt.models):
            continue
        if max(box[3] - box[0], box[4] - box[1]) >= MIN_BUILDING and box[5] - box[2] >= MIN_HEIGHT:
            things.append({'id': 'orig_' + ''.join(c if c.isalnum() else '_' for c in model['name']),
                           'title': 'only in the original', 'rebuilt': [], 'original': [model['name']], 'doors': []})
    for thing in things:
        boxes = [m['box'] for name in thing['rebuilt'] for m in by_name[name]]
        boxes += [m['box'] for m in original.models if m['name'] in thing['original']]
        thing['box'] = union(boxes)
        original_doors = [door for m in original.models if m['name'] in thing['original'] for door in m['doors']]
        thing['original_doors'] = []
        seen = set()
        for door in original_doors:
            near_rebuilt = any(math.hypot(door['at'][0] - d['at'][0], door['at'][1] - d['at'][1]) < 384
                               for d in thing['doors'])
            key = (round(door['at'][0] / 128), round(door['at'][1] / 128), door['event'])
            if near_rebuilt or key in seen:
                continue
            seen.add(key)
            thing['original_doors'].append(door)
    return things


def plan_views(scene, things, rebuilt_names):
    shots, skipped = [], []
    for thing in things:
        box = thing['box']
        own = {(1, name) for name in thing['rebuilt']} | {(0, name) for name in thing['original']}
        own |= {(i, m['name']) for i, side in enumerate(scene.sides) for m in side.models if overlaps(m['box'], box)}
        middle = [(box[0] + box[3]) / 2, (box[1] + box[4]) / 2, (box[2] + box[5]) / 2]
        width, depth = box[3] - box[0], box[4] - box[1]
        views = []
        for index, door in enumerate(thing['doors'] + thing['original_doors']):
            original_door = index >= len(thing['doors'])
            label = (f'odoor{door.get("event", index)}' if original_door else ('door' if index == 0 else f'door{index + 1}'))
            nx, ny = door['normal']
            length = math.hypot(nx, ny) or 1
            nx, ny = nx / length, ny / length
            target = [door['at'][0], door['at'][1], door['floor'] + 200]
            views.append((label, target, (nx, ny), 900.0, (-ny, nx), 300.0, False))
        for label, direction, span, extent in (('n', (0, 1), width, depth), ('s', (0, -1), width, depth),
                                               ('e', (1, 0), depth, width), ('w', (-1, 0), depth, width)):
            distance = min(5000.0, max(800.0, span / 2 / math.tan(HALF_FOV) + extent / 2))
            lateral = (-direction[1], direction[0])
            for raised in (False, True):
                views.append((label + ('_up' if raised else ''), middle, direction, distance, lateral,
                              span / 2, raised))
        for label, target, direction, distance, lateral, span, raised in views:
            camera, why = place_view(scene, own, box, target, direction, distance, lateral, span, raised)
            if camera is None:
                skipped.append((thing['id'], label, why))
                continue
            shots.append({'thing': thing['id'], 'view': label, 'at': [round(v) for v in camera],
                          'yaw': round(yaw_to(camera, target), 4), 'pitch': round(pitch_to(camera, target), 2)})
    return shots, skipped


def write_tour(path, folder, shots, hour):
    commands = ', '.join(f'"{c}"' for c in ('render hud off', 'render actors off', 'render effects off',
                                             'sky weather 0', 'weather clear'))
    lines = [f'output_dir: "{folder}"', 'exit: true', 'settle_seconds: 1.8', 'shots:']
    for shot in shots:
        x, y, z = shot['at']
        lines.append(f'  - {{name: "{shot["key"]}", position: [{x}, {y}, {z}], yaw: {shot["yaw"]}, '
                     f'pitch: {math.radians(shot["pitch"]):.4f}, time: "{hour}", commands: [{commands}]}}')
    path.write_text('\n'.join(lines) + '\n')


def run_tour(world, map_name, root, tour, folder, count, tag, mount=None):
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    environment = dict(os.environ, SDL_AUDIODRIVER='dummy')
    command = [str(repo / 'tools/run_game.sh'), '--isolated', f'bshots{tag}{os.getpid()}', '--world', world,
               '--map', map_name, '--assets', str(root), '--warmup', '5', '--seconds', str(40 + 3 * count),
               '--set', f'debug.screenshot_tour_path={tour}'] + (['--extra-mount', str(mount)] if mount else [])
    run = subprocess.run(command, capture_output=True, text=True, env=environment, cwd=repo)
    (tour.parent / f'{tag}.run.log').write_text(run.stdout + run.stderr)
    taken = len(list(folder.glob('*.png')))
    print(f'{tag}: {map_name}: {taken} of {count} pictures (exit {run.returncode})')


def pair(left, right, caption, out):
    pictures = []
    for path in (left, right):
        if path is not None and path.is_file():
            pictures.append(Image.open(path).convert('RGB'))
        else:
            pictures.append(None)
    size = next((p.size for p in pictures if p is not None), (1280, 720))
    width = 800
    height = round(size[1] * width / size[0])
    sheet = Image.new('RGB', (2 * width + 8, height + 22), (16, 16, 20))
    draw = ImageDraw.Draw(sheet)
    for index, (picture, side) in enumerate(zip(pictures, ('original', 'rebuild'))):
        x = index * (width + 8)
        if picture is not None:
            sheet.paste(picture.resize((width, height), Image.LANCZOS), (x, 22))
        else:
            draw.text((x + 20, 60), 'no picture', fill=(255, 90, 90))
        draw.text((x + 4, 5), f'{side}: {caption}', fill=(235, 235, 235))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=88)


def contact(paths, out, columns=2):
    if not paths:
        return
    thumbs = [Image.open(p) for p in paths]
    width = 1000
    scaled = [t.resize((width, round(t.size[1] * width / t.size[0])), Image.LANCZOS) for t in thumbs]
    height = max(t.size[1] for t in scaled)
    rows = (len(scaled) + columns - 1) // columns
    sheet = Image.new('RGB', (columns * width, rows * height), (16, 16, 20))
    for index, thumb in enumerate(scaled):
        sheet.paste(thumb, ((index % columns) * width, (index // columns) * height))
    sheet.save(out, quality=85)


def main():
    arguments = sys.argv[1:]
    original_name = take_option(arguments, '--original')
    world = take_option(arguments, '--world')
    root = take_option(arguments, '--assets')
    original_root = take_option(arguments, '--orig-assets', str(repo / 'assets_dev'))
    out = take_option(arguments, '--out')
    build_file = take_option(arguments, '--build')
    places_file = take_option(arguments, '--places')
    only = take_option(arguments, '--only')
    hour = take_option(arguments, '--time', '12:00')
    no_game = take_flag(arguments, '--no-game')
    plan_only = take_flag(arguments, '--plan')
    mount = take_option(arguments, '--mount')
    if len(arguments) != 1 or not (original_name and world and root and out):
        sys.exit(__doc__)
    out = Path(out).resolve()
    work = out / 'raw'
    work.mkdir(parents=True, exist_ok=True)
    rebuilt_path = map_path(arguments[0], mount or root, world)
    original_path = map_path(original_name, original_root, world)
    if build_file is None:
        candidate = Path(arguments[0]).resolve().parent / 'build.json'
        build_file = candidate if candidate.is_file() else None
    build = json.loads(Path(build_file).read_text()) if build_file else {}
    if not build:
        print('no build.json: buildings are found by size only')

    original = Side(export(original_path, work / 'original.json'))
    rebuilt = Side(export(rebuilt_path, work / 'rebuilt.json'))
    scene = Scene(original, rebuilt)
    things = gather(original, rebuilt, build)
    if only:
        things = [t for t in things if t['id'] in only.split(',')]
    shots, skipped = plan_views(scene, things, None)
    places = yaml.safe_load(Path(places_file).read_text())['places'] if places_file else []
    for place in places:
        shots.append({'thing': 'places', 'view': place['name'], 'at': place['at'], 'yaw': place['yaw'],
                      'pitch': place.get('pitch', 0.0)})
    for index, shot in enumerate(shots):
        shot['key'] = f'{index:03d}'
    (work / 'shots.json').write_text(json.dumps({'shots': shots, 'skipped': skipped, 'things': things}, indent=1))
    tours = {}
    for tag, map_path_, map_root, map_mount in (('original', original_path, original_root, None),
                                                 ('rebuilt', rebuilt_path, root, mount)):
        tours[tag] = (work / f'{tag}.tour.yml', work / tag, map_path_.name, map_root, map_mount)
        write_tour(tours[tag][0], tours[tag][1], shots, hour)
    print(f'{len(things)} buildings, {len(shots)} views, {len(skipped)} skipped; tours in {work}')
    if plan_only:
        return
    if not no_game:
        for tag, (tour, folder, map_name, map_root, map_mount) in tours.items():
            run_tour(world, map_name, map_root, tour, folder, len(shots), tag, map_mount)

    def picture(tag, key):
        found = sorted(tours[tag][1].glob(f'*-{key}.png')) or sorted(tours[tag][1].glob(f'{key}.png'))
        return found[0] if found else None

    by_thing = {}
    for shot in shots:
        target = out / shot['thing'] / f'{shot["view"]}.jpg'
        x, y, z = shot['at']
        pair(picture('original', shot['key']), picture('rebuilt', shot['key']),
             f'{shot["thing"]} {shot["view"]} ({x}, {y}, {z}, yaw {shot["yaw"]}, pitch {shot["pitch"]})', target)
        by_thing.setdefault(shot['thing'], []).append(target)
    for name, paths in by_thing.items():
        contact(paths, out / name / 'contact.jpg')
    lines, rows, listed = [], [], []
    for thing in things + ([{'id': 'places', 'title': 'given places', 'rebuilt': [], 'original': []}]
                           if places else []):
        views = [s['view'] for s in shots if s['thing'] == thing['id']]
        missed = [f'{view} ({why})' for name, view, why in skipped if name == thing['id']]
        listed.append({'id': thing['id'], 'title': thing['title'], 'rebuilt': list(thing['rebuilt']),
                       'original': list(thing['original']), 'views': views, 'skipped': missed,
                       'pictures': [f'{thing["id"]}/{view}.jpg' for view in views
                                    if (out / thing['id'] / f'{view}.jpg').is_file()],
                       'contact': f'{thing["id"]}/contact.jpg' if (out / thing['id'] / 'contact.jpg').is_file()
                       else None})
        lines.append(f'{thing["id"]}: {thing["title"]}; rebuild {", ".join(thing["rebuilt"]) or "-"}; original '
                     f'{", ".join(thing["original"]) or "-"}; views {" ".join(views)}'
                     + (f'; skipped {"; ".join(missed)}' if missed else ''))
        rows.append(f'<h2>{html.escape(thing["id"])} {html.escape(thing["title"])}</h2><p>rebuild '
                    f'{html.escape(", ".join(thing["rebuilt"]) or "-")}; original '
                    f'{html.escape(", ".join(thing["original"]) or "-")}'
                    + (f'; skipped {html.escape("; ".join(missed))}' if missed else '') + '</p>'
                    + (f'<a href="{thing["id"]}/contact.jpg"><img src="{thing["id"]}/contact.jpg" width="1000"></a>'
                       if views else ''))
    (out / 'index.txt').write_text('\n'.join(lines) + '\n')
    (out / 'index.json').write_text(json.dumps({'original': original_path.name, 'rebuilt': rebuilt_path.name,
                                                'views': len(shots), 'buildings': listed}, indent=1) + '\n')
    (out / 'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Building shots</title>'
                                    '<body style="background:#111;color:#ddd;font-family:sans-serif">'
                                    + '\n'.join(rows) + '</body>\n')
    print(f'index: {out / "index.html"}')


if __name__ == '__main__':
    main()
