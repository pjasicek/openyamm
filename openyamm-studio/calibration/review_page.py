#!/usr/bin/env python3
"""Writes the review page of the Map Studio's results: output/studio_review/index.html.

Rebuilt dungeons beside their originals (the same schematic render of both, and the comparison's numbers), the
in-game pictures of the shapes gallery, and the dungeon an evaluation agent built. Run after
`tests/run_shapes.sh --shots`; everything else is rendered here. Open the page in a browser: it is one folder of
static files and reads nothing from the network.
"""
import html
import json
import shutil
import subprocess
from pathlib import Path

studio = Path(__file__).resolve().parents[1]
repo = studio.parent
out = repo / 'output/studio_review'
images = out / 'img'
oymap = studio / 'build/oymap'
assets = repo / 'assets_dev'
COMPARED = [
    ('mm7_7d06', 'mm7', '7d06.blv', 'Temple of the Moon'),
    ('mm8_d05', 'mm8', 'd05.blv', 'Abandoned Temple'),
    ('mm7_7d23', 'mm7', '7d23.blv', 'The Lincoln'),
    ('mm6_scifi', 'mm6', 'sci-fi.blv', 'Control Center'),
    ('mm6_hive', 'mm6', 'hive.blv', 'The Hive'),
    ('mm6_cd2', 'mm6', 'cd2.blv', 'Castle Darkmoor'),
    ('mm6_6d18', 'mm6', '6d18.blv', "Gharik's Forge"),
    ('mm6_6d16', 'mm6', '6d16.blv', "Warlord's Fortress"),
]
DUNGEONS = [
    ('mm7_7d06', 'mm7', '7d06.blv', 'Temple of the Moon', 'Emerald Island, MM7'),
    ('mm6_6d16', 'mm6', '6d16.blv', "Warlord's Fortress", 'MM6'),
]
ROWS = [
    ('scale.floor_area_millions', 'Floor area (millions of square units)'),
    ('play.walkable_area_millions', 'Area the party can walk'),
    ('scale.sector_height.median', 'Typical room height'),
    ('scale.doorway_width.median', 'Typical doorway width'),
    ('scale.doorway_height.median', 'Typical doorway height'),
    ('scale.floor_level.spread', 'Lowest to highest floor'),
    ('structure.loops', 'Loops in the room graph'),
]
SHOTS = [
    ('01-hall-pillar-dais', 'The L-shaped hall: pillar, dais (stepped onto), and the far wall with its own surface'),
    ('02-hall-bend', "Round the hall's inner corner"),
    ('03-corridor-bend', 'The corridor drawn as a path, at its bend'),
    ('04-stairs-up', 'Eight steps up; the doorway at the top begins at the upper floor'),
    ('05-gallery-closet-door', 'The hinged door, shut'),
    ('06-stairs-down', 'The same flight from above'),
    ('07-ramp-down', 'The ramp down to the cave'),
    ('08-cave', 'The cave: an outline that bends inward, with rough walls'),
    ('09-cave-island', 'A rock island in the cave: the party walks round it'),
    ('10-grotto-mouth', 'An open mouth: the cave runs into the grotto with no doorway'),
    ('11-hall-split-level', 'A split-level hall: sunken floor, gallery, parapets, two flights with side walls'),
    ('12-hall-sunken-floor-dome', 'From the sunken floor: the raised ceiling drum above, the flight ahead'),
    ('13-hall-bookcase-parapet', 'A bookcase block: books on its long sides, a carved panel on its end'),
    ('14-gabled-doorway', 'A pointed arch with shoulders through a thick wall, the split-level hall beyond'),
    ('15-altar-bowl-raking-walls', 'An altar from three stacked blocks (stem, flaring bowl, rim); in front, a stair side wall with a raking top'),
    ('16-dome-ring-ribs', 'Looking up: a stone ring and two ribs across the opening of the raised ceiling'),
    ('17-level-against-walls', 'A raised level that bends round the room and stands against its walls, a chest on it'),
    ('18-ramp-parallel-ceiling', 'New: a ramp whose ceiling slopes with its floor'),
    ('19-loft-lean-to-hole-stairwell', 'New: a loft with a hole in its floor and a stairwell coming up through it'),
    ('20-loft-lean-to-raking-walls', 'New: a lean-to ceiling; the walls end on its slope'),
    ('21-floor-hole-from-below', 'New: the hole in the loft floor seen from the room below'),
    ('22-stairwell-from-its-foot', 'New: the stairwell from its foot, open to the loft above'),
    ('23-stairwell-from-the-loft', 'New: the same stairwell looking down from the loft'),
    ('24-stacked-doorways', 'New: two doorways one above the other in one wall'),
    ('25-pyramid-roof', 'New: a ceiling that narrows to a point (a pyramid roof)'),
    ('26-leaning-dome-raking-ribs', 'New: a dome whose sides lean in, with ribs that rake up its inside'),
    ('27-shrine-pyramid-lantern-cap', 'Newer: a lantern standing on a pyramid roof (a ceiling level on a level)'),
    ('28-shrine-leaning-side-brick', 'Newer: leaning ceiling sides with their texture in level rows, unstretched'),
    ('29-shrine-slab-chests-flight', 'Newer: a chest standing on a raised slab, and a flight up to it'),
    ('30-shrine-stairwell-and-hole', 'Newer: a floor hole under a pyramid roof'),
    ('31-tube-gable-end-west', 'Newer: a doorway in the end wall under a ridge ceiling'),
    ('32-tube-gable-end-east', 'Newer: the other end of the same ridge'),
    ('33-steep-ceiling', 'Newer: a ceiling that slopes steeply'),
    ('34-crypt-haunch-and-hole', 'Newer: a raking beam cut level where it meets the ceiling'),
    ('35-coffer-over-steps', 'Newer: a raised ceiling panel over a stepped room'),
    ('36-panels-bookcase-corner-strips', 'Newest: a bookcase panel on a wall and dark strips at its corners'),
    ('37-panels-fitted-and-wood', 'Newest: a full-height panel and a wooden one'),
    ('38-panels-sign-over-door-back', 'Newest: a panel over a door; the door is wood on this side'),
    ('39-panels-door-front', 'Newest: the same door carved on its front'),
    ('40-climb-foot', 'Newest: a bent tunnel that climbs, from its foot'),
    ('41-climb-bend', 'Newest: floor and ceiling raking round the bend'),
    ('42-climb-from-top', 'Newest: the same tunnel from its head'),
    ('43-climb-threshold', 'Newest: a doorway with a wooden threshold'),
    ('44-flight-treads-coping', 'Newest: wooden treads on a flight and a coping on its side walls'),
    ('45-threshold-stepped-treads', 'Newest: wooden treads on a stepped room'),
    ('46-works-doors-shut', 'Moving parts: three doors shut (left, two leaves that part up and down; middle, two leaves that part sideways; right, one leaf that slides sideways)'),
    ('47-works-doors-parting', 'Moving parts: the same three doors half a second after their events'),
    ('48-works-doors-open', 'Moving parts: the same three doors open'),
    ('49-works-pair-door-open-close', 'Moving parts: the two-leaf door from close by'),
    ('50-gate-block-up-plate', 'Moving parts: a gate block standing in a passage, and the plate that sinks it'),
    ('51-gate-block-sunk-tram-below', 'Moving parts: the block sunk into the floor; beyond it a tram at the foot of its slope'),
    ('52-tram-at-the-ledge', 'Moving parts: the tram after it has travelled up its slanting line to the ledge'),
    ('53-wall-section-shut', 'Moving parts: a section of wall, from wall to wall and floor to ceiling, that slides aside'),
    ('54-wall-section-in-its-pocket', 'Moving parts: the wall section slid sideways into its pocket'),
    ('55-pod-lift-down', 'Moving parts: a lift that is a thin floor, down, under a hole in the deck above'),
    ('56-pod-lift-raised-open-shaft', 'Moving parts: the same lift raised; the shaft under it is open'),
    ('57-pod-lift-from-the-deck', 'Moving parts: the lift seen from the deck it rises to'),
    ('58-bridge-aside', 'Moving parts: a bridge with kerbs lying aside, along the wall of a pit'),
    ('59-bridge-between-the-mouths', 'Moving parts: the bridge slid sideways between the two mouths'),
    ('60-bridge-from-the-hall', 'Moving parts: the bridge from the hall it leads out of'),
    ('61-growing-bridge-stub', 'Moving parts: a bridge that grows, as a stub'),
    ('62-growing-bridge-grown', 'Moving parts: the same bridge grown across the pit'),
    ('63-dome-mouth-two-parts', 'Round three: one mouth between two domed rooms, full width to the eaves and a pointed part above, with no bar between'),
    ('64-dome-mouth-from-the-north', 'Round three: the same mouth from the other room'),
    ('65-water-pool-kerb-ring', 'Round three: a water floor in a sunken pool, inside a closed ring of kerb'),
    ('66-hollow-floor-one-plane', 'Uneven floors: a cave whose whole floor is one tilted plane, not square to any wall; the block and the pillar stand on it'),
    ('67-hollow-from-its-east-mouth', 'Uneven floors: the same cave from its east mouth; the doorways keep level sills'),
    ('68-hollow-banks-and-roof', 'Uneven floors: a level floor with rock banks up to the walls and a roof that comes down to their rim'),
    ('69-trench-banks', 'Uneven floors: a trench with sloping banks instead of upright sides'),
    ('70-funnel-and-mound', 'Uneven floors: a funnel that slopes down on all sides, and a mound'),
    ('71-wedge-ramp-to-the-loft', 'Uneven floors: a wedge as a ramp up to a raised doorway'),
    ('72-buttress-and-twisted-block', 'Uneven floors: a raking buttress, and a block with a different height at each corner'),
    ('73-landings-and-open-flight', 'Uneven floors: two landings one above the other; the upper flight starts on the lower landing and is open underneath'),
    ('74-tunnel-mouth-in-the-hall', 'Tunnels: a six-sided tunnel mouth in a hall wall, with no lintel or jambs'),
    ('75-tunnel-six-sided', 'Tunnels: inside the tunnel, with the cross-section measured from the Hive (narrow floor, sides leaning out and in again)'),
    ('76-tunnel-side-doorway', 'Tunnels: a doorway in the side of a tunnel'),
    ('77-tunnel-ramp-side-doorway', 'Tunnels: a doorway in the side of a climbing stretch'),
    ('78-tunnel-mitred-bend', 'Tunnels: a bend, mitred as the original mitres its bends'),
    ('79-tunnel-plate-joint-and-square-end', 'Tunnels: a floor plate across the tunnel, and the run toward its square end'),
    ('80-tunnel-square-end', 'Tunnels: a tunnel ending square at a doorway, as the Hive ends tunnels at doors'),
    ('81-tube-mouth-in-the-cell', 'Tunnels: an eight-sided tube (the Control Center kind) entering a room'),
    ('82-tube-banks', 'Tunnels: the tube inside; its low banks are shallow enough to walk'),
    ('83-tube-rising-ceiling-back', 'Tunnels: the tube under a ceiling that rises along it'),
    ('84-guard-post-monster-item-podium-notice', 'Contents: a monster placed at his post (peaceful, he stays there), a key lying on the floor, a podium and a wall panel that are clicked'),
    ('85-rig-lever-on-post-gate-shut', 'Contents: a lever on a post, and a gate, shut'),
    ('86-rig-gate-halves-parting', 'Contents: the gate parting; its upper half rises into the ceiling'),
    ('87-rig-wall-button-pushed-in', 'Contents: a button pushed into its wall'),
    ('88-rig-deck-up-chest-posts-button', 'Contents: a deck that has risen with its posts, a chest riding on it and a button on its side'),
    ('89-gully-mouth-follows-bank-and-roof', 'Caves: a mouth between two caves that follows the bank of the floor and the lean of the roof'),
    ('90-gully-mouth-from-the-bank', 'Caves: the same mouth from the bank; the bank is rock, the level floor is tile'),
    ('91-gully-hanging-ramp-slab', 'Caves: a smooth ramp hanging between two landings, open underneath'),
    ('92-arch-on-the-bank', 'Caves: an arch whose sill follows the sloping floor'),
    ('93-vault-mouth-and-flight-into-it', 'An arch as high as the vault it opens into, and stairs that end in the doorway'),
    ('94-vault-mouth-from-the-apse', 'The same arch from the other side'),
    ('95-crown-tunnel', 'A tunnel whose cross-section comes to a point at the top'),
    ('96-false-floor-and-unseen-floor', 'A floor the party falls through, and below it one the party stands on and cannot see'),
    ('97-apse-switched-lights-and-plates', 'Lights that events switch on and off, by plates in the floor'),
    ('98-pit-ladder-and-glow', 'A ladder down a pit, with a pulsing light'),
    ('99-dais-over-uneven-floor', 'A raised dais standing over a floor that sags'),
    ('100-desk-with-its-own-top', 'A chest with a top of its own (a desk)'),
    ('101-leaf-fold-shut', 'Door leaves: two leaves, each with its own picture, shut'),
    ('102-leaf-seal-shut', 'Door leaves: one seal painted across two leaves in four quarters, shut'),
    ('103-leaf-pass-shut', 'Door leaves: an upper and a lower half, shut'),
    ('104-leaf-mirror-shut', 'Door leaves: the right leaf the mirror of the left'),
    ('105-leaf-fold-folding', 'Door leaves: the two leaves folding into their jambs, without wall room beside the doorway'),
    ('106-leaf-seal-folding', 'Door leaves: the seal parting as its leaves fold away'),
    ('107-leaf-pass-passing', 'Door leaves: the halves passing each other'),
    ('108-leaf-part-open', 'Door leaves: a door that opens only part of its way'),
    ('109-item-spawn-and-sided-door', 'A random item on the floor (rolled when the map is entered), and a door that does something different from each side'),
    ('110-sided-door-open-guard-shown', 'The door opened from its one side; a guard who was hidden appears'),
    ('111-sided-guard-inside', 'The guard inside, carrying an item'),
    ('112-keg-and-screen-before', 'A keg (a decoration) that is clicked, and a screen across the cell'),
    ('113-keg-and-screen-after', 'After the keg: the screen repainted, and the party can walk through it'),
]
# Round three (2026-11-12): each rebuild's score when the round began, and at its end as the tool of that evening
# measured it. The score the page measures now may differ from the latter only by the measuring tool's own
# corrections of the same night (points on floor edges, ceiling seams, points inside shut blocks).
ROUND_THREE = {
    'mm6_scifi': (95.6, 97.8, 98.5), 'mm6_6d18': (95.4, 91.6, 98.7), 'mm7_7d23': (93.1, 94.3, 94.4),
    'mm6_hive': (92.7, 95.8, 96.7), 'mm8_d05': (88.4, 93.5, 94.4), 'mm6_cd2': (92.1, 92.3, 92.3),
    'mm7_7d06': (87.7, 88.6, 88.8),
}

MOVING = [
    ('gate-block', 'A gate block sinking into the floor. Upper row, before: the carving stays where it is and the block sinks through it. Lower row, now: the carving sinks with the block'),
    ('pod-lift', 'A lift rising past the camera (third picture: its edge). Before, its edge showed whatever part of the texture lay at that height; now it shows the part the project gave it'),
]


def run(*arguments):
    return subprocess.run([str(oymap), *map(str, arguments)], capture_output=True, text=True)


def main():
    images.mkdir(parents=True, exist_ok=True)
    sections = []
    for key, world, map_file, name, where in DUNGEONS:
        brief = repo / 'devdocs/map_studio/briefs' / key / 'L3'
        for view in ('plan', 'iso'):
            run('render', map_file, '--world', world, '--assets', assets, '--out', images / f'{key}.original.{view}.png',
                '--view', view, '--size', 1100, '--no-labels')
            run('render', brief, '--assets', assets, '--out', images / f'{key}.rebuilt.{view}.png',
                '--view', view, '--size', 1100, '--no-labels')
        compared = subprocess.run(['python3', str(studio / 'calibration/compare.py'), str(brief),
                                   str(studio / f'calibration/originals/{key}.metrics.json'), '--json'],
                                  capture_output=True, text=True)
        rows = {row['metric']: row for row in json.loads(compared.stdout)['rows']} if compared.returncode == 0 else {}
        table = ''.join(
            f'<tr><td>{html.escape(label)}</td><td class="n">{rows[metric]["original"]:g}</td>'
            f'<td class="n">{rows[metric]["rebuilt"]:g}</td></tr>'
            for metric, label in ROWS if metric in rows)
        pairs = ''.join(
            f'<div class="pair"><figure><img src="img/{key}.original.{view}.png" alt="">'
            f'<figcaption>Original, {caption}</figcaption></figure>'
            f'<figure><img src="img/{key}.rebuilt.{view}.png" alt="">'
            f'<figcaption>Rebuilt from the brief, {caption}</figcaption></figure></div>'
            for view, caption in (('iso', 'from above at an angle'), ('plan', 'plan')))
        sections.append(
            f'<section><h2>{html.escape(name)} <small>{html.escape(where)}</small></h2>{pairs}'
            f'<table><thead><tr><th></th><th>Original</th><th>Rebuilt</th></tr></thead><tbody>{table}</tbody></table>'
            '</section>')
    shots_source = repo / 'output/studio_shapes'
    for name in ('plan.png', 'iso.png'):
        if (shots_source / name).exists():
            shutil.copy(shots_source / name, images / f'shapes.{name}')
    shots = ''
    for stem, caption in SHOTS:
        source = shots_source / 'shots' / f'{stem}.png'
        if source.exists():
            shutil.copy(source, images / source.name)
            shots += (f'<figure><img src="img/{stem}.png" alt=""><figcaption>{html.escape(caption)}</figcaption>'
                      '</figure>')
    # Same-camera pictures of the original and the rebuild (calibration/ingame_compare.py).
    ingame = ''
    compare = repo / 'output/studio_temple/compare'
    for original in sorted((compare / 'original').glob('*.png')) if compare.exists() else []:
        rebuilt = compare / 'rebuilt' / original.name
        if not rebuilt.exists():
            continue
        label = original.stem.split('-', 1)[1].replace('-', ' ')
        for side, source in (('original', original), ('rebuilt', rebuilt)):
            shutil.copy(source, images / f'temple.{side}.{original.name}')
        ingame += (f'<div class="pair"><figure><img src="img/temple.original.{original.name}" alt="">'
                   f'<figcaption>Original: {html.escape(label)}</figcaption></figure>'
                   f'<figure><img src="img/temple.rebuilt.{original.name}" alt="">'
                   f'<figcaption>Rebuilt: {html.escape(label)}</figcaption></figure></div>')
    # The original's nave and library, brightened for inspection (output/studio_temple/nave/bright).
    nave = ''
    for picture in sorted((repo / 'output/studio_temple/nave/bright').glob('*.png')):
        shutil.copy(picture, images / f'nave.{picture.name}')
        label = picture.stem.split('-', 1)[1].replace('-', ' ')
        nave += (f'<figure><img src="img/nave.{picture.name}" alt=""><figcaption>{html.escape(label)}</figcaption>'
                 '</figure>')
    # Outdoor sketches (S4, first slice): the sketch's picture beside the original map's plan. The sketch pictures
    # are made by `oymap render-sketch`; the two here were rendered once from copies of the briefs with the
    # buildings' footprints moved into the plan, and are kept as they are.
    outdoor = ''
    for key, world, map_file, name in (('mm8_out02', 'mm8', 'out02.odm', 'Ravenshore'),
                                       ('mm7_7out02', 'mm7', '7out02.odm', 'Harmondale')):
        sketch = images / f'sketch.{key}.png'
        if not sketch.exists():
            continue
        run('render', map_file, '--world', world, '--assets', assets, '--out', images / f'{key}.original.plan.png',
            '--view', 'plan', '--size', 1100)
        if (images / f'outdoor.{key}.rebuilt.iso.png').exists():
            outdoor += (f'<h3>{html.escape(name)}: the land</h3><div class="pair">'
                        f'<figure><img src="img/outdoor.{key}.original.iso.png" alt="">'
                        '<figcaption>The original map (buildings orange)</figcaption></figure>'
                        f'<figure><img src="img/outdoor.{key}.rebuilt.iso.png" alt="">'
                        '<figcaption>Built from the sketch: heights and water only</figcaption></figure></div>')
        outdoor += (f'<h3>{html.escape(name)}: the sketch</h3><div class="pair"><figure><img src="img/{key}.original.plan.png" alt="">'
                    '<figcaption>The original map: terrain by height, buildings numbered</figcaption></figure>'
                    f'<figure><img src="img/sketch.{key}.png" alt="">'
                    '<figcaption>The sketch: land, water, roads, districts, building plots, named places</figcaption>'
                    '</figure></div>')
    # Outdoor rebuilds measured against their originals (output/studio_s4b: scratch sketches corrected from the
    # originals by script, a calibration of the builder and the measure).
    outdoor_measured = ''
    outdoor_oymap = oymap
    for key, world, map_file, name, sheets in (
            ('mm8_out02', 'mm8', 'out02.odm', 'Ravenshore', (
                ('studio_s4d/ingame_final_r/diff/01-market-from-south.png', 'The town from the south: original, rebuild, and their outlines laid over each other. Both now stand under the same sky; the crystal is in its place (taken over from the original as a model); houses of several parts with their roofs, the council hall with its stair, the fountain, paved streets, grass between the houses, townsfolk. The big trees in the foreground are missing'),
                ('studio_s4d/ingame_final_r/diff/02-lanes-from-south.png', 'The lanes, the river and the town bridge'),
                ('studio_s4d/ingame_final_r/diff/06-square-from-east.png', 'The square from the east'),
                ('studio_s4d/ingame_forms_after/diff/02-hostel-from-south-east.png', 'A house with cut corners, built with its true outline and roof (it was a full box that swallowed a chest)'))),
            ('mm7_7out02', 'mm7', '7out02.odm', 'Harmondale', (
                ('studio_s4d/ingame_final_h/diff/01-town-from-south.png', 'The town from the south: the houses, the eight-sided tower, the wells and streets on their hill, under the original\'s sky'),
                ('studio_s4d/ingame_final_h/diff/05-hamlet.png', 'The hamlet'),
                ('studio_s4d/ingame_final_h/diff/06-fort-from-south.png', 'The hill fort, the original\'s broken ring of walls'),
                ('studio_cal/mm7_7out02/ingame_worst_f/diff/08-region-H8.png', 'A weak place (picture from before the sky was fixed): the rugged rim of the map, outside where the party walks'))),
            ):
        project = repo / 'devdocs/map_studio/briefs' / key / 'L4'
        if not (project / 'project.yml').exists():
            continue
        folder = repo / 'output/studio_compare' / key
        done = subprocess.run([str(outdoor_oymap), 'compare', map_file, '--world', world, '--with', str(project),
                               '--assets', str(assets), '--out', str(folder), '--json'],
                              capture_output=True, text=True)
        report = folder / 'report.json'
        if done.returncode != 0 or not report.exists():
            continue
        totals = json.loads(report.read_text())
        summary = totals.get('totals', totals)
        score = summary.get('score')
        parts = totals.get('parts', summary.get('parts', []))
        line = f'{score * 100:.1f} % overall' if isinstance(score, (int, float)) else ''
        figures = ''
        for picture, caption in (('heights.png', 'Heights: where the rebuilt land agrees with the original and where it does not'),
                                 ('ground.png', 'Ground, water and roads'), ('objects.png', 'Buildings, decorations, spawn points and events')):
            if (folder / picture).exists():
                shutil.copy(folder / picture, images / f'outdoor.compare.{key}.{picture}')
                figures += (f'<figure><img src="img/outdoor.compare.{key}.{picture}" alt=""><figcaption>'
                            f'{html.escape(caption)}</figcaption></figure>')
        pairs = ''
        for sheet, caption in sheets:
            source = repo / 'output' / sheet
            if source.exists():
                target = f'outdoor.pair.{key}.{source.name}'
                shutil.copy(source, images / target)
                pairs += f'<figure><img src="img/{target}" alt=""><figcaption>{html.escape(caption)}</figcaption></figure>'
        outdoor_measured += (f'<h3>{html.escape(name)} <small>{html.escape(line)}</small></h3>'
                             f'<div class="shots">{figures}</div><div class="shots" style="grid-template-columns: 1fr">'
                             f'{pairs}</div>')
    # The automatic comparison (`oymap compare`): every rebuild that has a project, with its score and maps.
    measured = ''
    round_rows = ''
    for key, world, map_file, name in COMPARED:
        project = repo / 'output/studio_temple/project' if key == 'mm7_7d06' else \
            repo / 'devdocs/map_studio/briefs' / key / 'L4'
        if not (project / 'project.yml').exists():
            continue
        folder = repo / 'output/studio_compare' / key
        done = run('compare', map_file, '--world', world, '--with', project, '--assets', assets, '--out', folder,
                   '--json')
        report = folder / 'report.json'
        if done.returncode != 0 or not report.exists():
            measured += f'<h3>{html.escape(name)}</h3><p>The rebuild does not build yet.</p>'
            continue
        totals = json.loads(report.read_text())
        for picture in ('geometry.png', 'textures.png'):
            shutil.copy(folder / picture, images / f'compare.{key}.{picture}')
        worst = ''.join(
            f'<li>{html.escape("; ".join(point["differs"]) if isinstance(point.get("differs"), list) else str(point.get("differs", "")))}</li>'
            for point in totals.get('worst_points', [])[:5])
        summary = totals.get('totals', totals)
        if key in ROUND_THREE and isinstance(summary.get('score'), (int, float)):
            before, after, corrected = ROUND_THREE[key]
            round_rows += (f'<tr><td>{html.escape(name)}</td><td class="n">{before:.1f} %</td>'
                           f'<td class="n">{after:.1f} %</td><td class="n">{corrected:.1f} %</td>'
                           f'<td class="n"><strong>{summary["score"] * 100:.1f} %</strong></td></tr>')
        line = ', '.join(f'{label} {summary[field] * 100:.0f} %' for field, label in
                         (('score', 'overall'), ('distance_agreement', 'shape'), ('texture_agreement', 'textures'))
                         if isinstance(summary.get(field), (int, float)))
        measured += (f'<h3>{html.escape(name)} <small>{html.escape(line)}</small></h3><div class="pair">'
                     f'<figure><img src="img/compare.{key}.geometry.png" alt=""><figcaption>Shape: green where the '
                     'rebuild agrees with the original, red where it does not; numbered are the worst places'
                     '</figcaption></figure>'
                     f'<figure><img src="img/compare.{key}.textures.png" alt=""><figcaption>Textures</figcaption>'
                     f'</figure></div><ol>{worst}</ol>')
    # Textures on moving parts, before and after the fix of 2026-11-12 (three moments each, same camera).
    moving = ''
    for stem, caption in MOVING:
        source = repo / 'output/studio_shapes/moving_textures' / f'sheet_{stem}.png'
        if source.exists():
            shutil.copy(source, images / f'moving.{stem}.png')
            moving += (f'<figure><img src="img/moving.{stem}.png" alt=""><figcaption>{html.escape(caption)}'
                       '</figcaption></figure>')
    # A new dungeon built from its written brief, with no original (devdocs/xeen/briefs/xd01/L4).
    xeen = ''
    second_shots = repo / 'output/studio_cal/xd01/shots2'
    xeen_shots = repo / 'output/studio_cal/xd01/shots3'
    if not xeen_shots.exists():
        xeen_shots = second_shots
    captions = xeen_shots / 'captions.yml'
    # Before and after: the first pass's weakest pictures beside the second pass's answer to them.
    xeen_pairs = ''
    for first, second, caption in (
            ('11-hall-loft-stair.png', '12-hall-loft-stair.png', 'The loft stair: cramped and all one plank colour in the first pass; now an open flight with hand rails, posts and lantern light'),
            ('09-hall-from-barn-doors.png', '10-hall-from-barn-doors.png', 'The grain hall from the barn doors: bare in the first pass; now posts, chandeliers, the loft along the whole wall and a gutter in the sagging floor'),
            ('21-cistern-lever-heart-gate.png', '25-pen-through-bars.png', 'A slime pen: solid gates hid what was in them; now real bars, and the pen behind them')):
        a = repo / 'output/studio_cal/xd01/shots' / first
        b = second_shots / second
        if a.exists() and b.exists():
            shutil.copy(a, images / f'xd01.first.{a.name}')
            shutil.copy(b, images / f'xd01.second.{b.name}')
            xeen_pairs += (f'<div class="pair"><figure><img src="img/xd01.first.{a.name}" alt=""><figcaption>First pass'
                           f'</figcaption></figure><figure><img src="img/xd01.second.{b.name}" alt=""><figcaption>'
                           f'Second pass: {html.escape(caption)}</figcaption></figure></div>')
    # The texture pass (2026-11-13): the second pass's pictures beside the same cameras after it.
    texture_pairs = ''
    for name, caption in (
            ('10-hall-from-barn-doors.png', 'The grain hall: the loft front of ship windows and the grey castle stone are gone; the Pirate Outpost\'s hall brick, panelling and plank roof'),
            ('06-bay-crates.png', 'The bay: the Pirate Outpost\'s storeroom, panelled wainscot with planks above, flagstones and its crates'),
            ('01-dock-arrival.png', 'The loading dock where the party arrives'),
            ('08-office-desk.png', 'Joe\'s office: the Pirate Outpost\'s plaster over carved panelling and its bookcase'),
            ('42-outfall-river-grate.png', 'The culvert\'s river grate: it had a sci-fi panel from the Control Center; now the Free Haven Sewer\'s stone and grate')):
        a = second_shots / name
        b = xeen_shots / name
        if a.exists() and b.exists() and xeen_shots != second_shots:
            shutil.copy(a, images / f'xd01.pass2.{a.name}')
            shutil.copy(b, images / f'xd01.tex.{b.name}')
            texture_pairs += (f'<div class="pair"><figure><img src="img/xd01.pass2.{a.name}" alt=""><figcaption>'
                              f'Second pass</figcaption></figure><figure><img src="img/xd01.tex.{b.name}" alt="">'
                              f'<figcaption>Texture pass: {html.escape(caption)}</figcaption></figure></div>')
    if texture_pairs:
        xeen_pairs += ('<h3>Second pass and texture pass</h3><p>After your note on the ship windows: each area now takes '
                       'its textures from one shipped dungeon whose purpose fits. The warehouse upstairs is built '
                       'from the Pirate Outpost\'s wood (MM8), as it uses it; the cellar and culvert from the Free '
                       'Haven Sewer\'s stone (MM6), the cistern keeping its brick. 46 textures where there were 50, '
                       'and 5 from no shipped dungeon where there were 23: the five are Joe\'s painted signs, which '
                       'nothing shipped has; they and six more are on a list of textures to generate (the signs, a '
                       'red-painted heart gate, a glass bug tank, a rack of bottles).</p>' + texture_pairs)
    if captions.exists():
        for name in ('iso.png', 'plan.png'):
            if (xeen_shots / name).exists():
                shutil.copy(xeen_shots / name, images / f'xd01.{name}')
        for line in captions.read_text().splitlines():
            if ': ' not in line or line.lstrip().startswith('#'):
                continue
            name, caption = line.split(': ', 1)
            source = xeen_shots / name.strip()
            if source.exists():
                shutil.copy(source, images / f'xd01.{source.name}')
                xeen += (f'<figure><img src="img/xd01.{source.name}" alt=""><figcaption>'
                         f'{html.escape(caption.strip().strip(chr(34)))}</figcaption></figure>')
    # The second new dungeon from its brief (devdocs/xeen/briefs/xd02/L4).
    xeen2 = ''
    xd02_first = repo / 'output/studio_cal/xd02/shots'
    xd02_shots = repo / 'output/studio_cal/xd02/shots2'
    if not (xd02_shots / 'captions.yml').exists():
        xd02_shots = xd02_first
    xd02_pairs = ''
    for name, caption in (
            ('12-turntable.png', 'The turntable cavern: Snergle\'s Caverns\' worked red rock on the walls, its raw dark rock overhead'),
            ('28-stope-floor-benches.png', 'The stope from its floor: red benches against dark walls instead of one busy red rock everywhere'),
            ('19-chapel.png', 'The chapel: the dwarves\' halls of Snergle\'s Iron Mines'),
            ('01-adit-arrival.png', 'The adit where the party arrives'),
            ('32-spider-galleries.png', 'The spider galleries in natural blue-grey rock')):
        a = xd02_first / name
        b = xd02_shots / name
        if a.exists() and b.exists() and xd02_shots != xd02_first:
            shutil.copy(a, images / f'xd02.pass1.{a.name}')
            shutil.copy(b, images / f'xd02.tex.{b.name}')
            xd02_pairs += (f'<div class="pair"><figure><img src="img/xd02.pass1.{a.name}" alt=""><figcaption>'
                           f'First pass</figcaption></figure><figure><img src="img/xd02.tex.{b.name}" alt="">'
                           f'<figcaption>Texture pass: {html.escape(caption)}</figcaption></figure></div>')
    if xd02_pairs:
        xeen2 = ('</div><h3>First pass and texture pass</h3><p>The mine now takes its textures from MM6\'s two Snergle '
                 'maps, a dwarves\' mine and its halls: Snergle\'s Caverns for the drifts, stopes, caves and camp '
                 '(a worked red rock, a raw dark rock and a natural blue-grey one, instead of one busy red rock on '
                 'nearly half the walls), Snergle\'s Iron Mines for the chapel, tally room and strongroom, and MM7\'s '
                 'Red Dwarf Mines for the gold, iron and bedding neither has. Textures from no shipped dungeon fell '
                 'from 10 to 3; ten are listed to be generated (gold seams in each rock, an ore-cart side, the pools\' '
                 'crusted basins, chalked tallies). Still weak: the rails and the cage are bright new steel, the carts '
                 'read as crates, the stope from below still reads as tiers.</p>' + xd02_pairs + '<div class="shots">')
    if (xd02_shots / 'captions.yml').exists():
        for name in ('iso.png', 'plan.png'):
            if (xd02_shots / name).exists():
                shutil.copy(xd02_shots / name, images / f'xd02.{name}')
        for line in (xd02_shots / 'captions.yml').read_text().splitlines():
            if ': ' not in line or line.lstrip().startswith('#'):
                continue
            name, caption = line.split(': ', 1)
            source = xd02_shots / name.strip()
            if source.exists():
                shutil.copy(source, images / f'xd02.{source.name}')
                xeen2 += (f'<figure><img src="img/xd02.{source.name}" alt=""><figcaption>'
                          f'{html.escape(caption.strip().strip(chr(34)))}</figcaption></figure>')
    # The third new dungeon from its brief (devdocs/xeen/briefs/xd03/L4).
    xeen3 = ''
    xd03_shots = repo / 'output/studio_cal/xd03/shots'
    if (xd03_shots / 'captions.yml').exists():
        for name in ('iso.png', 'plan.png'):
            if (xd03_shots / name).exists():
                shutil.copy(xd03_shots / name, images / f'xd03.{name}')
        for line in (xd03_shots / 'captions.yml').read_text().splitlines():
            if ': ' not in line or line.lstrip().startswith('#'):
                continue
            name, caption = line.split(': ', 1)
            source = xd03_shots / name.strip()
            if source.exists():
                shutil.copy(source, images / f'xd03.{source.name}')
                xeen3 += (f'<figure><img src="img/xd03.{source.name}" alt=""><figcaption>'
                          f'{html.escape(caption.strip().strip(chr(34)))}</figcaption></figure>')
    crypt = repo / 'output/studio_eval/run3/crypt_c'
    crypt_picture = ''
    if crypt.exists():
        run('render', crypt, '--assets', assets, '--out', images / 'crypt.iso.png', '--view', 'iso', '--size', 1100)
        crypt_picture = '<figure><img src="img/crypt.iso.png" alt=""><figcaption>Numbers are rooms; S is the arrival; the red frame is the lever-operated door</figcaption></figure>'
    (out / 'index.html').write_text(PAGE.replace('@DUNGEONS@', ''.join(sections)).replace('@SHOTS@', shots)
                                    .replace('@CRYPT@', crypt_picture).replace('@INGAME@', ingame).replace('@NAVE@', nave).replace('@OUTDOOR@', outdoor).replace('@MEASURED@', measured).replace('@MOVING@', moving).replace('@ROUND@', round_rows).replace('@OUTDOORMEASURED@', outdoor_measured).replace('@XEEN@', xeen).replace('@XEENPAIRS@', xeen_pairs).replace('@XEEN2@', xeen2).replace('@XEEN3@', xeen3))
    print(out / 'index.html')


PAGE = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Map Studio review</title>
<style>
:root { --bg: #f4f1ea; --ink: #23201b; --soft: #6b6458; --line: #d8d1c2; --card: #fffdf8; --accent: #7a4b12; }
@media (prefers-color-scheme: dark) {
  :root { --bg: #17161a; --ink: #e9e4d8; --soft: #a39b8b; --line: #34323a; --card: #1f1e23; --accent: #e0b070; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 16px/1.55 Georgia, "Times New Roman", serif; }
main { max-width: 1500px; margin: 0 auto; padding: 28px 16px 80px; }
h1 { font-size: 30px; margin: 0 0 6px; }
h2 { font-size: 23px; margin: 46px 0 10px; border-top: 1px solid var(--line); padding-top: 22px; }
h3 { font-size: 18px; margin: 22px 0 6px; }
h2 small { font-size: 15px; color: var(--soft); font-weight: normal; margin-left: 8px; }
p { max-width: 70ch; margin: 8px 0; }
.lead { color: var(--soft); }
ol.ask { max-width: 75ch; padding-left: 22px; }
ol.ask li { margin: 8px 0; }
ol { max-width: 110ch; font-size: 14px; color: var(--soft); }
.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 12px 0; }
.shots { display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); gap: 12px; }
figure { margin: 0; background: var(--card); border: 1px solid var(--line); border-radius: 6px; overflow: hidden; }
figure img { display: block; width: 100%; height: auto; background: #1b1b1f; cursor: zoom-in; }
figcaption { padding: 7px 10px; font-size: 14px; color: var(--soft); }
table { border-collapse: collapse; margin: 14px 0; font-size: 15px; }
th, td { padding: 5px 14px 5px 0; border-bottom: 1px solid var(--line); text-align: left; }
td.n, th:not(:first-child) { text-align: right; font-variant-numeric: tabular-nums; }
.note { border-left: 3px solid var(--accent); padding: 2px 0 2px 14px; margin: 14px 0; max-width: 75ch; }
dialog { border: 0; padding: 0; background: #000; max-width: 96vw; max-height: 96vh; }
dialog img { display: block; max-width: 96vw; max-height: 96vh; cursor: zoom-out; }
dialog::backdrop { background: rgba(0, 0, 0, 0.85); }
@media (max-width: 800px) { .pair { grid-template-columns: 1fr; } .shots { grid-template-columns: 1fr; } }
</style></head><body><main>
<h1>Map Studio: what to look at</h1>
<p class="lead">Indoor and outdoor maps from project files. Shown here: the fix for textures on moving parts,
seven shipped dungeons rebuilt as projects and measured against their originals, the Temple of the Moon in the
game beside the original, every room shape and moving part of the test map in the game (the newest at the end:
uneven cave floors and tunnels with a cross-section), two outdoor maps built from sketches and measured against
their originals, and a dungeon an agent built from one paragraph. Click a picture to enlarge it.</p>

<h2>Textures on moving parts <small>what you pointed at on 2026-11-12: fixed</small></h2>
<p>On doors, lifts and other moving parts built by the studio the texture stood still in the world while the part
moved, so it seemed to slide across the part. The game treats a moving face the way the original maps need: it
lays the texture out from the face's place in the world unless the map says the texture moves with the door, and
the studio never said so. It now does, for every sliding part, and also tells the game where on the part the
texture belongs. Doors whose texture is stretched to fit the leaf were never affected. Each sheet below shows
three moments from one camera: the upper row before the fix, the lower row now.</p>
<div class="shots" style="grid-template-columns: 1fr">@MOVING@</div>

<h2>A new dungeon from a written brief <small>Joe's Warehouse, the first Xeen dungeon; no original to copy from</small></h2>
<p>Everything further down this page was rebuilt from a shipped map that the agent could measure. This one was
not: an agent was given the written brief of Joe's Warehouse (a warehouse over a cellar; a sixteen-sided cistern
with six slime pens behind gates that one lever opens; an invoice crate the story wants; a door that opens with a
key or a sharp eye; a culvert out to the river, opened from inside) and built it; a second agent then took it
through a second pass with what the studio had learned in between. It is 26 rooms; the game plays it from the
loading dock to the river in a scripted walk of 110 steps with a party that needs the key, and in a short one with
a party sharp-eyed enough to open the doors without it (both pass four runs of four); it opens up in the order
the brief plans.</p>
<div class="pair">
<figure><img src="img/xd01.iso.png" alt=""><figcaption>The dungeon from above at an angle</figcaption></figure>
<figure><img src="img/xd01.plan.png" alt=""><figcaption>Its plan</figcaption></figure>
</div>
<h3>First pass and second pass</h3>
@XEENPAIRS@
<div class="note"><strong>What to know before judging it.</strong> The Xeen world does not exist in the game yet,
so it stands in MM7's: giant rats for the slimes (every slime in MM6 to 8 is immune to weapons and far too strong
for a first dungeon), dragonflies for the bugs, MM7 keys and a bill of sale for the invoice. Since the first pass:
the upstairs is one family of wood (the texture pass above), lights fall in pools with dark corners between, the pens are behind real bars and the
lever lifts all six and starts a flashing lamp, there is a ladder, a secret stash, and the culvert turns at a drain
shaft with daylight and a rats' nest on the way out. Still weak: the boss pair, because the game ignores the hit
points a placed monster is given (a game-side matter, not the map's), and the map is silent, because MM7 has no
sound files of the kind the studio places. Signs are carved plaques with no words on them; what they say shows
when the party points at them.</div>
<div class="shots">@XEEN@</div>

<h2>A second new dungeon from its brief <small>the Red Dwarf Mines; no original to copy from</small></h2>
<p>Built the same way, by an agent that had read how Joe's Warehouse went: a mine of 43 rooms on seven floor
levels, with a cart that rides a timber trestle over a chasm (the party rides it, called by levers at either end),
a second cart on a drowned line that runs only when the points are set, a funnel stope with railed ledges round
its pit and a hoist cage, four coloured pools that raise a character once, six gold veins (mining the rich one
opens a burrow), a rockfall, a winch that clears the west adit, and a brake key for the deep exit. The game plays
it end to end in a scripted walk of 171 steps (four runs of four pass), and it opens up in the order the brief
plans. Six small rooms are never walked into by design (bunk shelves and ore chutes).</p>
<div class="pair">
<figure><img src="img/xd02.iso.png" alt=""><figcaption>The mine from above at an angle</figcaption></figure>
<figure><img src="img/xd02.plan.png" alt=""><figcaption>Its plan</figcaption></figure>
</div>
<div class="note"><strong>What to know before judging it.</strong> It stands in MM7's world like Joe's Warehouse:
dwarven soldiers for the mad dwarves (MM7 counts dwarves as the party's friends, so a script makes this clan
hostile), troglodytes for the tiger moles. Good, by the agent's judgement and mine: the trestle ride, the view
over the stope from its rim, the chapel and the tally room. Weak (in the first pass): one busy red rock texture covered a third of
all walls, so the stope seen from below was a dark drum of blocky tiers (the texture pass below answers this); the
caves are plain shells; the carts and the
winch are boxes; the mine is silent; the dwarves come in packs harder than the brief's party should meet.</div>
<div class="shots">@XEEN2@</div>

<h2>A third new dungeon from its brief <small>the Deep Mine; the first built under the texture rule</small></h2>
<p>The Red Dwarves' deep workings and their Clan King's hall: 24 rooms over 2,000 units of height. The party arrives
on a ledge and rides a cart down a timber trestle; a furnace hall with a slag channel, two bridges and a gallery
where a sentry rings a gong unless he is killed first (the gong opens the barracks and lights its torches); two
levers that lift the bars of the King's Gate; the King's six-sided hall with its dais, dome and gutters that turn to
slag when his guard falls; the hoard behind his key; a cage that carries the party 1,536 up the escape shaft; a
geode with bat queens, gem clusters that pay once and a secret singing wall. Two scripted walks (175 and 46 steps)
pass four runs of four each, and it opens up in the order the brief plans. It is the first new dungeon built after
your note on Joe's Warehouse: every one of its 39 textures is used by a shipped dungeon, one family per area (the
mine from MM7's Red Dwarf Mines, the forge and the King's hall from Gharik's Forge, the geode from Snergle's
Caverns, the vault from Stone City), and five it lacks are listed to be generated (blue quartz, a crystal cavity,
a bronze gong face, the clan crest, glowing slag).</p>
<div class="pair">
<figure><img src="img/xd03.iso.png" alt=""><figcaption>The mine from above at an angle</figcaption></figure>
<figure><img src="img/xd03.plan.png" alt=""><figcaption>Its plan</figcaption></figure>
</div>
<div class="note"><strong>What to know before judging it.</strong> Good, by the agent's judgement and mine: the cart ride,
the gallery over the furnace hall, the two-lever gate opening on the throne, the cage ride. Weak: the King is an
ordinary dwarf of 100 hit points (the game ignores the 300 written) who never leaves his dais, so the second phase is
lights and burning gutters, not a frenzy; the dome is grey stone, not glittering crystal; the furnace hall's walls are
large plain planes; the cart is a plank box on block wheels; the mine is silent; all dwarves share one model. Still
built before the studio's fix of what you found in the Forge, so its levers are flat plates.</div>
<div class="shots">@XEEN3@</div>

<h2>Measured by tool <small>no person needed: this is what the rebuild agents steer by</small></h2>
<p>The tool stands at points all over the original's floors, looks in 50 directions in both maps and compares
what it sees: how far away, and which texture. A rebuild appears here once its project exists.</p>
<h3>Rounds three to five <small>2026-11-12 evening to 2026-11-13 night</small></h3>
<table><thead><tr><th>Dungeon</th><th>Before round three</th><th>After round three, measured as before</th>
<th>After round three, corrected measure</th><th>Now, after round five</th></tr></thead><tbody>@ROUND@</tbody></table>
<div class="note"><strong>Round five</strong> was about what is in the rooms and what happens there, which the
measure does not see, so the numbers barely move. Three of the seven originals place no monster at a fixed spot
and leave no item lying; their monsters come from spawn points. What had gone unread for four rounds was the
chests: they now hold the originals' items, among them the Control Center's Control Cube and the Abandoned
Temple's quest items (one had been taken for the wrong book since the first round). Placed where the original has
them: the Temple of the Moon's four guards and its moon tile, the Lincoln's seventeen droids, Castle Darkmoor's
Lich King and 72 items, the Hive's Reactor and Queen, whose deaths now drive its ending. Not yet sayable: random
items on the floor (each map has some), a monster that carries an item.</div>
<div class="note"><strong>Round four</strong> used what was built between the rounds: tunnels with their true
cross-section (the Hive's are six-sided, measured; the Control Center's tubes and the Lincoln's corridors
eight-sided), cave floors and roofs given by heights at points, sloping banks, wedges, stairs open underneath,
arches into vaults. Castle Darkmoor's caves took their shape (98.6 %) and lost textures: an uneven floor can
carry one surface only, so its rock banks show floor tile, and its three cavern junctions stand as rock walls
because a mouth cannot yet follow an uneven roof. Both are being built now.</div>
<div class="note">Seven agents each took one dungeon further with what the studio learned that day: moving parts
of every kind, tunnels that climb, panels on walls, treads and thresholds. <strong>Gharik's Forge fell under the
old measure for an honest reason:</strong> earlier rounds had made slabs and stairs 2 to 4 units too wide, because
the measure stood some of its points exactly on their edges and a wider slab caught them. This round put every
shape back on the original's lines. The measure was then corrected (points stand clear of floor edges; rays no
longer slip through seams in ceilings; points inside a shut gate are left out), which is the last column. What
still costs most: cave floors that tilt and twist (Temple of the Moon, Castle Darkmoor's caves), and the Hive's
tunnels, which are rectangles where the original's have sloping lower and upper sides.</div>
@MEASURED@

<h2>What I would like you to judge</h2>
<ol class="ask">
<li><strong>Do the rebuilt dungeons read as the same places?</strong> They were drawn by an agent from a written
brief, without the original's geometry. Look at overall shape, the proportion of rooms to corridors, and where
they are plainly wrong. Flat ceilings, missing doors and objects, and the missing dome of the Temple are known.</li>
<li><strong>Are the stairs, ramp, hinged door and pillar acceptable as engine geometry</strong> in the in-game
pictures? Not whether the test map is pretty: it has one theme and lights that are far too bright.</li>
<li><strong>Is this the right next step:</strong> take the Temple from shell to a playable rebuild (doors, chests,
monsters, lights, textures) and show it beside the original from the same camera positions in the game?</li>
</ol>

@DUNGEONS@

<h2>Temple of the Moon in the game <small>the same camera position in both maps</small></h2>
<p>The rebuild now has its doors, chests, monster spawns and textures, loads in the game and is walked. These
pictures are taken standing on the floor at the same map position, looking the same way.</p>
<div class="note"><strong>State of these pictures:</strong> after round four (measured likeness in the
table above; 37 rooms, playtest 257 steps). New in this take: the caves have uneven floors and roofs, given by
heights at the places where the rock changes slope (the north cavern: 23 floor points and 41 roof points, one
room where it was four); the passages, the anteroom arms and the stair run have their pointed vaults; the west
steps have the original's five treads. Still different: cave mouths are rectangles cut to the roof's lowest
point where the original's follow the roof; three mouths have level sills where the original's rake; the rock
islands of the south cavern have no banks at their foot; steep rock wears the floor's texture; the dome's bands
are straight; the four guards and the moon tile are not placed.</div>
@INGAME@

<h2>The original's nave and library, looked at closely <small>brightened; the game shows them much darker</small></h2>
<p>What the nave is, measured from the map: a sunken floor in the middle, a gallery 128 units higher all round it
behind a low parapet, a flight of six steps with side walls at each end, columns and wall niches on the gallery,
a ceiling 640 above the floor with a round opening into a dome drum that rises another 650. The library's
bookcases are free-standing blocks: books on the long sides, a carved panel on each end.</p>
<div class="shots">@NAVE@</div>

<div class="note">The colours are only there to tell rooms apart; they differ between the two pictures. Red frames
in an original are its doors and moving parts. A rebuilt flight of stairs is a room of its own, so rebuilt
dungeons show more rooms than the originals.</div>

<h2>The new room shapes, in the game <small>openyamm-studio/examples/shapes_gallery</small></h2>
<p>One small test map with one of each. The game walks it in a scripted run that checks the party's height on the
dais, on the steps, on the lift, on the ramp and in the cave.</p>
<div class="pair">
<figure><img src="img/shapes.iso.png" alt=""><figcaption>The test map: 4 hall, 2 corridor, 6 stairs, 3 gallery, 7 closet, 5 ramp, 1 cave</figcaption></figure>
<figure><img src="img/shapes.plan.png" alt=""><figcaption>Its plan</figcaption></figure>
</div>
<div class="shots">@SHOTS@</div>
<div class="note">The last eight pictures (placed monsters and items, things on moving parts, cave mouths that
follow the rock, a hanging ramp) are not in the seven rebuilt dungeons yet: that is the next round.</div>

<h2>Outdoor maps, first steps <small>the sketch, and terrain built from it</small></h2>
<p>An outdoor map starts as a sketch: where the land rises, where the water is, the road lines, the districts and
the plot of every building, the named places and the fights. These two were drawn from the originals by the
brief's author; the tool now checks them (ids, overlapping plots, roads meeting their junctions, heights within
their bands) and draws them. From a sketch the tool now builds a classic outdoor map with its land and water
only: the game loads both and the party walks on them. Roads, buildings, ground textures, trees and monsters are
not built yet, and the rebuilt land is smoother than the original: plateaus are flat where the original is
rugged.</p>
<h3>Since the evening of 2026-11-12: a whole outdoor map from a sketch, measured against its original</h3>
<p>From a sketch the studio now builds the land, the ground tiles with shores, roads in their beds, buildings in
several parts with the wall panels and roofs the shipped towns use, towers, walls with gates, bridges, wells,
fountains, chests and signs, townsfolk and monsters, and the way off the map's edges into its neighbours; the
game walks both maps, opens houses and chests through what was built, leaves by an edge and comes back. A new
measure compares a rebuilt outdoor map with its original in ten parts (heights, relief, cliffs, water, ground,
roads, buildings, decorations, spawn points, events, and since the morning of 2026-11-13 the rim). Ravenshore
went from 36 % to 91 % and Harmondale from 25 % to 86 % as measured until that morning; the land beyond the
walkable square, which the party only ever sees as a skyline, is now judged by that skyline and no longer height by
height, which with the maps unchanged gives Ravenshore 90 % and Harmondale 88 % (the figures beside the names).</p>
<div class="note"><strong>Read these with three things in mind.</strong> The first sketches were written from the
original maps by script (heights on a coarse grid, road beds, each building's parts and sizes, where monsters
and people stand); an agent then went through each map place by place with the measure, as for the dungeons. So
this shows what the builder can build from a careful description of a known map; a map drawn from a written
brief alone is not tried yet. Second, the measure was made stricter during the night: trees and rocks are now
paired with the original's one by one, where before only their number per region counted, which was right by
construction; that part fell from 97 to 99 % to about 94 %, and totals from before are not comparable. Third,
the grey sky of the earlier pictures was a missing table row, not weather: a rebuilt map had no continent and so
no sky of its own. That is fixed, and the ships and the crystal are taken over from the original as models for
now. Not built: the rugged rim outside the walkable land (Harmondale's heights are 85 % inside it and 68 % in
the rim), one roof over a hall that is not convex, an arcade.</div>
@OUTDOORMEASURED@
<h3>The first sketches <small>earlier the same day</small></h3>
@OUTDOOR@

<h2>A dungeon built by an agent from one paragraph <small>"The Old Crypt"</small></h2>
<p>A fresh agent that had never seen the tools was given a paragraph: an L-shaped antechamber, a corridor with a
bend, stairs down, a crypt with two pillars and a dais, a side chamber behind a door that only a lever opens, two
chests. It built this through the tools in 59 calls; the game plays its own test from arrival to both chests.</p>
<div class="pair">@CRYPT@</div>

<dialog id="zoom"><img alt=""></dialog>
<script>
const zoom = document.getElementById('zoom');
document.querySelectorAll('figure img').forEach((image) => image.addEventListener('click', () => {
  zoom.querySelector('img').src = image.src;
  zoom.showModal();
}));
zoom.addEventListener('click', () => zoom.close());
</script>
</main></body></html>
'''

main()
